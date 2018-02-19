from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

from .utils import send_activation_email


def convert_full_name_to_parts(defaults):
    full_name = defaults.pop('full_name', ' ')
    first_name, *last_name = full_name.split(' ')
    if first_name:
        defaults.update(first_name=first_name)
    if last_name:
        defaults.update(last_name=' '.join(last_name))
    return defaults


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        extra_fields = convert_full_name_to_parts(extra_fields)
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

    def get_or_create(self, defaults, **kwargs):
        # Allow passing of 'full_name' but replace it with actual database fields
        defaults = convert_full_name_to_parts(defaults)
        return super().get_or_create(defaults=defaults, **kwargs)

    def get_or_create_and_notify(self, defaults=dict(), site=None, **kwargs):
        defaults.update(is_active=False)
        user, created = self.get_or_create(defaults=defaults, **kwargs)
        if created:
            send_activation_email(user, site)
        return user, created


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    email = models.EmailField(_('email address'), unique=True)
    REQUIRED_FIELDS = []

    # Remove the username field which is no longer used
    username = None

    objects = UserManager()

    def __str__(self):
        return self.get_full_name()
