from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group
from django.db import models
from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.core.fields import RichTextField

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
from .utils import send_activation_email


class UserQuerySet(models.QuerySet):
    def staff(self):
        return self.filter(
            Q(groups__name=STAFF_GROUP_NAME) | Q(is_superuser=True)
        ).distinct()

    def staff_admin(self):
        return self.filter(groups__name=TEAMADMIN_GROUP_NAME)

    def reviewers(self):
        return self.filter(groups__name=REVIEWER_GROUP_NAME)

    def partners(self):
        return self.filter(groups__name=PARTNER_GROUP_NAME)

    def community_reviewers(self):
        return self.filter(groups__name=COMMUNITY_REVIEWER_GROUP_NAME)

    def applicants(self):
        return self.filter(groups__name=APPLICANT_GROUP_NAME)

    def approvers(self):
        return self.filter(groups__name=APPROVER_GROUP_NAME)

    def finances(self):
        return self.filter(groups__name=FINANCE_GROUP_NAME)

    def contracting(self):
        return self.filter(groups__name=CONTRACTING_GROUP_NAME)


class UserManager(BaseUserManager.from_queryset(UserQuerySet)):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

    def get_or_create_and_notify(self, defaults=dict(), site=None, **kwargs):
        # Set a temp password so users can access the password reset function if needed.
        temp_pass = BaseUserManager().make_random_password(length=32)
        temp_pass_hash = make_password(temp_pass)
        defaults.update(password=temp_pass_hash)
        user, created = self.get_or_create(defaults=defaults, **kwargs)
        if created:
            send_activation_email(user, site)
            applicant_group = Group.objects.get(name=APPLICANT_GROUP_NAME)
            user.groups.add(applicant_group)
            user.save()
        return user, created


class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    full_name = models.CharField(verbose_name=_('Full name'), max_length=255, blank=True)
    slack = models.CharField(
        verbose_name=_('Slack name'),
        blank=True,
        help_text=_('This is the name we should "@mention" when sending notifications'),
        max_length=50,
    )

    # Meta: used for migration purposes only
    drupal_id = models.IntegerField(null=True, blank=True, editable=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    # Remove the username/first/last name field which is no longer used.
    username = None
    first_name = None
    last_name = None

    objects = UserManager()

    def __str__(self):
        return self.get_full_name() if self.get_full_name() else self.get_short_name()

    def get_full_name(self):
        return self.full_name.strip()

    def get_short_name(self):
        return self.email

    def get_full_name_with_group(self):
        is_apply_staff = f' ({STAFF_GROUP_NAME})' if self.is_apply_staff else ''
        is_reviewer = f' ({REVIEWER_GROUP_NAME})' if self.is_reviewer else ''
        is_applicant = f' ({APPLICANT_GROUP_NAME})' if self.is_applicant else ''
        is_finance = f' ({FINANCE_GROUP_NAME})' if self.is_finance else ''
        is_contracting = f' ({CONTRACTING_GROUP_NAME})' if self.is_contracting else ''
        return f'{self.full_name.strip()}{is_apply_staff}{is_reviewer}{is_applicant}{is_finance}{is_contracting}'

    @cached_property
    def roles(self):
        return list(self.groups.values_list('name', flat=True))

    @cached_property
    def is_apply_staff(self):
        return self.groups.filter(name=STAFF_GROUP_NAME).exists() or self.is_superuser

    @cached_property
    def is_apply_staff_admin(self):
        return self.groups.filter(name=TEAMADMIN_GROUP_NAME).exists() or self.is_superuser

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
    def is_contracting(self):
        return self.groups.filter(name=CONTRACTING_GROUP_NAME).exists()

    class Meta:
        ordering = ('full_name', 'email')

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.full_name} ({self.email})>'


@register_setting
class UserSettings(BaseSetting):
    class Meta:
        verbose_name = 'user settings'

    consent_show = models.BooleanField(
        'Show consent checkbox',
        default=False,
    )

    consent_text = models.CharField(
        max_length=255,
        blank=True,
    )

    consent_help = RichTextField(blank=True)

    extra_text = RichTextField(blank=True)

    panels = [
        MultiFieldPanel([
            FieldPanel('consent_show'),
            FieldPanel('consent_text'),
            FieldPanel('consent_help'),
        ], 'consent checkbox on login form'),
        MultiFieldPanel([
            FieldPanel('extra_text'),
        ], 'extra text on login form'),
    ]
