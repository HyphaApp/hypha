from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from .groups import (APPLICANT_GROUP_NAME, APPROVER_GROUP_NAME,
                     COMMUNITY_REVIEWER_GROUP_NAME, PARTNER_GROUP_NAME,
                     REVIEWER_GROUP_NAME, STAFF_GROUP_NAME)
from .utils import send_activation_email


def get_compliance_sentinel_user():
    """
    Get the sentinel User for unauthenticated Submission and Project pages.

    The unauthenticated Submission and Project pages need to track when they
    are accessed by Compliance.  However the Event models User FK is
    non-nullabe.  Changing that relation to nullable and fixing it around the
    site is prohibitively costly so we've opted to use a sentinel User.
    """
    return User.objects.get(email='compliance-sentinel')


def get_finance_sentinel_user():
    """
    Get the sentinel User for unauthenticated PaymentRequest pages.

    The unauthenticated PaymentRequest pages need to track when they are
    accessed by Finance.  However the Event models User FK is non-nullabe.
    Changing that relation to nullable and fixing it around the site is
    prohibitively costly so we've opted to use a sentinel User.
    """
    return User.objects.get(email='finance-sentinel')


class UserQuerySet(models.QuerySet):
    def staff(self):
        return self.filter(
            Q(groups__name=STAFF_GROUP_NAME) | Q(is_superuser=True)
        ).distinct()

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
    full_name = models.CharField(verbose_name='Full name', max_length=255, blank=True)
    slack = models.CharField(
        verbose_name='Slack name',
        blank=True,
        help_text='This is the name we should "@mention" when sending notifications',
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

    def get_absolute_url(self):
        return reverse('wagtailusers_users:edit', args=(self.id,))

    def __str__(self):
        return self.get_full_name() if self.get_full_name() else self.get_short_name()

    def get_full_name(self):
        return self.full_name.strip()

    def get_short_name(self):
        return self.email

    @cached_property
    def roles(self):
        return list(self.groups.values_list('name', flat=True))

    @cached_property
    def is_apply_staff(self):
        return self.groups.filter(name=STAFF_GROUP_NAME).exists() or self.is_superuser

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

    class Meta:
        ordering = ('full_name', 'email')

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.full_name} ({self.email})>'
