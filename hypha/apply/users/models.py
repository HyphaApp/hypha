from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group
from django.core import exceptions
from django.db import IntegrityError, models
from django.db.models.constants import LOOKUP_SEP
from django.db.models.utils import resolve_callables
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.fields import RichTextField

from .groups import (
    APPLICANT_GROUP_NAME,
    APPROVER_GROUP_NAME,
    COMMUNITY_REVIEWER_GROUP_NAME,
    CONTRACTING_GROUP_NAME,
    FINANCE_GROUP_NAME,
    PARTNER_GROUP_NAME,
    REVIEWER_GROUP_NAME,
    STAFF_GROUP_NAME,
    TEAMADMIN_GROUP_NAME,
)
from .utils import get_user_by_email, is_user_already_registered, send_activation_email


class UserQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def staff(self):
        return self.filter(groups__name=STAFF_GROUP_NAME, is_active=True)

    def staff_admin(self):
        return self.filter(groups__name=TEAMADMIN_GROUP_NAME, is_active=True)

    def reviewers(self):
        return self.filter(groups__name=REVIEWER_GROUP_NAME, is_active=True)

    def partners(self):
        return self.filter(groups__name=PARTNER_GROUP_NAME, is_active=True)

    def community_reviewers(self):
        return self.filter(groups__name=COMMUNITY_REVIEWER_GROUP_NAME, is_active=True)

    def applicants(self):
        return self.filter(groups__name=APPLICANT_GROUP_NAME, is_active=True)

    def approvers(self):
        return self.filter(groups__name=APPROVER_GROUP_NAME, is_active=True)

    def finances(self):
        return self.filter(groups__name=FINANCE_GROUP_NAME, is_active=True)

    def finances_level_1(self):
        return self.filter(groups__name=FINANCE_GROUP_NAME, is_active=True).exclude(
            groups__name=APPROVER_GROUP_NAME
        )

    def finances_level_2(self):
        return self.filter(groups__name=FINANCE_GROUP_NAME, is_active=True).filter(
            groups__name=APPROVER_GROUP_NAME
        )

    def contracting(self):
        return self.filter(groups__name=CONTRACTING_GROUP_NAME, is_active=True)


class UserManager(BaseUserManager.from_queryset(UserQuerySet)):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        is_registered, reason = is_user_already_registered(email)
        if is_registered:
            raise ValueError(reason)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)

    def _extract_model_params(self, defaults, **kwargs):
        """
        Prepare `params` for creating a model instance based on the given kwargs;
        A copied method from model's query.py; for use by get_or_create_and_notify().
        """
        defaults = defaults or {}
        params = {k: v for k, v in kwargs.items() if LOOKUP_SEP not in k}
        params.update(defaults)
        property_names = self.model._meta._property_names
        invalid_params = []
        for param in params:
            try:
                self.model._meta.get_field(param)
            except exceptions.FieldDoesNotExist:
                # It's okay to use a model's property if it has a setter.
                if not (param in property_names and getattr(self.model, param).fset):
                    invalid_params.append(param)
        if invalid_params:
            raise exceptions.FieldError(
                "Invalid field name(s) for model %s: '%s'."
                % (
                    self.model._meta.object_name,
                    "', '".join(sorted(invalid_params)),
                )
            )
        return params

    def get_or_create_and_notify(
        self, defaults: dict | None = None, site=None, **kwargs
    ):
        """Create or get an account for applicant and send activation email to applicant.

        Args:
            defaults: Dict containing user attributes for user creation. Defaults to dict().
            site: current site for sending activation email. Defaults to None.

        Raises:
            IntegrityError: if multiple account exist with same email

        Returns:
            A tuple containing a user instance and a boolean that indicates
            whether the user was created or not.
        """
        _created = False

        if defaults is None:
            defaults = {}

        email = kwargs.get("email")
        redirect_url = ""
        if "redirect_url" in kwargs:
            redirect_url = kwargs.pop("redirect_url")

        is_registered, _ = is_user_already_registered(email=email)

        if is_registered:
            user = get_user_by_email(email=email)
            # already handled in PageStreamBaseForm.
            if not user:
                raise IntegrityError("Found multiple account")
            elif not user.is_active:
                raise IntegrityError("Found an inactive account")
        else:
            if "password" in kwargs:
                # Coming from registration without application
                temp_pass = kwargs.pop("password")
            else:
                temp_pass = BaseUserManager().make_random_password(length=32)

            temp_pass_hash = make_password(temp_pass)

            defaults.update(password=temp_pass_hash)
            try:
                params = dict(
                    resolve_callables(self._extract_model_params(defaults, **kwargs))
                )
                user = self.create(**params)
            except IntegrityError:
                raise

            send_activation_email(user, site, redirect_url=redirect_url)
            _created = True

        applicant_group = Group.objects.get(name=APPLICANT_GROUP_NAME)
        if applicant_group not in user.groups.all():
            user.groups.add(applicant_group)
            user.save()
        return user, _created


class User(AbstractUser):
    email = models.EmailField(_("email address"), unique=True)
    full_name = models.CharField(
        verbose_name=_("Full name"), max_length=255, blank=True
    )
    slack = models.CharField(
        verbose_name=_("Slack name"),
        blank=True,
        help_text=_('This is the name we should "@mention" when sending notifications'),
        max_length=50,
    )

    # Meta: used for migration purposes only
    drupal_id = models.IntegerField(null=True, blank=True, editable=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    # Remove the username/first/last name field which is no longer used.
    username = None
    first_name = None
    last_name = None

    objects = UserManager()

    wagtail_reference_index_ignore = True

    def __str__(self):
        return self.get_full_name() if self.get_full_name() else self.get_short_name()

    def get_full_name(self):
        return self.full_name.strip()

    def get_short_name(self):
        return self.email

    def get_full_name_with_group(self):
        is_apply_staff = f" ({STAFF_GROUP_NAME})" if self.is_apply_staff else ""
        is_reviewer = f" ({REVIEWER_GROUP_NAME})" if self.is_reviewer else ""
        is_applicant = f" ({APPLICANT_GROUP_NAME})" if self.is_applicant else ""
        is_finance = f" ({FINANCE_GROUP_NAME})" if self.is_finance else ""
        is_contracting = f" ({CONTRACTING_GROUP_NAME})" if self.is_contracting else ""
        return f"{self.full_name.strip()}{is_apply_staff}{is_reviewer}{is_applicant}{is_finance}{is_contracting}"

    @cached_property
    def roles(self):
        return list(self.groups.values_list("name", flat=True))

    @cached_property
    def is_apply_staff(self):
        return self.groups.filter(name=STAFF_GROUP_NAME).exists() or self.is_superuser

    @cached_property
    def is_apply_staff_or_finance(self):
        return self.is_apply_staff or self.is_finance

    @cached_property
    def is_apply_staff_admin(self):
        return (
            self.groups.filter(name=TEAMADMIN_GROUP_NAME).exists() or self.is_superuser
        )

    @cached_property
    def is_reviewer(self):
        return self.groups.filter(name=REVIEWER_GROUP_NAME).exists()

    @cached_property
    def is_partner(self):
        return self.groups.filter(name=PARTNER_GROUP_NAME).exists()

    @cached_property
    def is_community_reviewer(self):
        return self.groups.filter(name=COMMUNITY_REVIEWER_GROUP_NAME).exists()

    @cached_property
    def is_applicant(self):
        return self.groups.filter(name=APPLICANT_GROUP_NAME).exists()

    @cached_property
    def is_approver(self):
        return self.groups.filter(name=APPROVER_GROUP_NAME).exists()

    @cached_property
    def is_finance(self):
        return self.groups.filter(name=FINANCE_GROUP_NAME).exists()

    @cached_property
    def is_finance_level_1(self):
        return (
            self.groups.filter(name=FINANCE_GROUP_NAME).exists()
            and not self.groups.filter(name=APPROVER_GROUP_NAME).exists()
        )

    @cached_property
    def is_finance_level_2(self):
        # disable finance2 user if invoice flow in not extended
        if not settings.INVOICE_EXTENDED_WORKFLOW:
            return False
        return (
            self.groups.filter(name=FINANCE_GROUP_NAME).exists()
            & self.groups.filter(name=APPROVER_GROUP_NAME).exists()
        )

    @cached_property
    def is_contracting(self):
        return self.groups.filter(name=CONTRACTING_GROUP_NAME).exists()

    @cached_property
    def is_contracting_approver(self):
        return (
            self.groups.filter(name=CONTRACTING_GROUP_NAME).exists()
            and self.groups.filter(name=APPROVER_GROUP_NAME).exists()
        )

    def get_absolute_url(self):
        """Used in the activities messages to generate URL for user instances.

        Returns:
           url pointing to the wagtail admin, as there are no public urls for user.
        """
        return reverse("wagtailusers_users:edit", args=[self.id])

    class Meta:
        ordering = ("full_name", "email")

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.full_name} ({self.email})>"


@register_setting
class AuthSettings(BaseGenericSetting):
    wagtail_reference_index_ignore = True

    class Meta:
        verbose_name = "Auth Settings"

    consent_show = models.BooleanField(_("Show consent checkbox?"), default=False)
    consent_text = models.CharField(max_length=255, blank=True)
    consent_help = RichTextField(blank=True)
    extra_text = RichTextField(
        _("Login extra text"),
        blank=True,
        help_text=_("Displayed along side login form"),
    )
    register_extra_text = RichTextField(
        blank=True, help_text=_("Extra text to be displayed on register form")
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("consent_show"),
                FieldPanel("consent_text"),
                FieldPanel("consent_help"),
            ],
            _("User consent on login & register forms"),
        ),
        MultiFieldPanel(
            [
                FieldPanel("extra_text"),
            ],
            _("Login form customizations"),
        ),
        MultiFieldPanel(
            [
                FieldPanel("register_extra_text"),
            ],
            _("Register form customizations"),
        ),
    ]
