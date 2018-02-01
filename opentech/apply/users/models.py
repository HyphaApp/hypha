from django.db import models
from django.contrib.auth.models import AbstractUser

from .utils import send_activation_email


class User(AbstractUser):
    full_name = models.CharField(verbose_name='Full name', max_length=255, blank=True)

    class Meta:
        unique_together = ('email',)

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        if self.full_name:
            return self.full_name.strip()

        return super().get_full_name()

    def get_user_by_email(self, email):
        email_field = getattr(self, 'EMAIL_FIELD', 'email')
        return self.objects.filter(**{email_field + '__iexact': email})

    @classmethod
    def get_or_create_new(cls, defaults, **kwargs):
        defaults.update(is_active=False)
        user, created = cls.objects.get_or_create(defaults=defaults, **kwargs)
        if created:
            send_activation_email(user)
        return user
