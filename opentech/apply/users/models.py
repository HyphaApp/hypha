from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

from .groups import REVIEWER_GROUP_NAME, STAFF_GROUP_NAME
from .utils import send_activation_email


class UserQuerySet(models.QuerySet):
    def staff(self):
        return self.filter(groups__name=STAFF_GROUP_NAME)

    def reviewers(self):
        return self.filter(groups__name=REVIEWER_GROUP_NAME)


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
        defaults.update(is_active=False)
        user, created = self.get_or_create(defaults=defaults, **kwargs)
        if created:
            send_activation_email(user, site)
        return user, created


class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    full_name = models.CharField(verbose_name='Full name', max_length=255, blank=True)

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

    @property
    def is_apply_staff(self):
        return self.groups.filter(name=STAFF_GROUP_NAME).exists() or self.is_superuser

    @property
    def is_reviewer(self):
        return self.groups.filter(name=REVIEWER_GROUP_NAME).exists()

    class Meta:
        ordering = ('full_name', 'email')

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.full_name} ({self.email})>'
