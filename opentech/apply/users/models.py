from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    full_name = models.CharField(verbose_name='Full name', max_length=255, blank=True)

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        if self.full_name:
            return self.full_name.strip()

        return super().get_full_name()

