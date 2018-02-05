from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

from .utils import send_activation_email


def convert_full_name_to_parts(full_name):
    first_name, last_name = full_name.split(' ', 1)
    return first_name, last_name


class UserManager(BaseUserManager):
    def get_or_create(self, defaults, **kwargs):
        defaults.update(is_active=False)

        first_name, last_name = convert_full_name_to_parts(defaults.pop('full_name', ''))
        defaults.update(first_name=first_name, last_name=last_name)

        user, created = super().get_or_create(defaults=defaults, **kwargs)
        if created:
            send_activation_email(user)
        return user


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    email = models.EmailField(_('email address'), unique=True)
    REQUIRED_FIELDS = []

    objects = UserManager()
