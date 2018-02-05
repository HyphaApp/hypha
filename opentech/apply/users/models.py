from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

from .utils import send_activation_email


class UserManager(BaseUserManager):
    def get_or_create(self, defaults, **kwargs):
        defaults.update(is_active=False)
        user, created = super().get_or_create(defaults=defaults, **kwargs)
        if created:
            send_activation_email(user)
        return user


class User(AbstractUser):
    full_name = models.CharField(verbose_name='Full name', max_length=255, blank=True)

    objects = UserManager()

    class Meta:
        unique_together = ('email',)

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        if self.full_name:
            return self.full_name.strip()

        return super().get_full_name()
