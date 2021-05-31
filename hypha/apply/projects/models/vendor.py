from django.db import models
from django.utils.translation import gettext_lazy as _
from babel.numbers import list_currencies, get_currency_name

from hypha.apply.utils.storage import PrivateStorage
from hypha.apply.users.models import User


def due_diligence_documents(instance, filename):
    return f'vendor/{instance.vendor_id}/due_diligence_documents/{filename}'


class BankInformation(models.Model):
    CURRENCY_CHOICES = [
        (currency, f'{get_currency_name(currency)} - {currency}')
        for currency in list_currencies()
    ]

    account_holder_name = models.CharField(max_length=150)
    account_routing_number = models.CharField(max_length=10)
    account_number = models.CharField(max_length=20)
    account_currency = models.CharField(
        choices=CURRENCY_CHOICES,
        max_length=10
    )
    need_extra_info = models.BooleanField(default=False)
    branch_address = models.TextField(_('Address'), blank=True)
    iba_info = models.OneToOneField(
        'self',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='bank_info',
        verbose_name='Intermediary Bank Account Information'
    )
    nid_type = models.CharField(
        max_length=25,
        verbose_name='National Identity Document Type',
        blank=True
    )
    nid_number = models.CharField(
        max_length=20,
        blank=True
    )

    def __str__(self):
        return self.account_holder_name


class Vendor(User):

    TYPE_CHOICES = [
        ('organization', 'Organization'),
        ('personal', 'Personal'),
    ]

    contractor_name = models.CharField(max_length=150, blank=True)
    address = models.TextField(_('Address'), blank=True)
    type = models.CharField(max_length=15, choices=TYPE_CHOICES, blank=True)
    required_to_pay_taxes = models.BooleanField(default=False)
    bank_info = models.OneToOneField(
        BankInformation,
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    other_info = models.TextField(blank=True)

    def __str__(self):
        return self.full_name


class DueDiligenceDocument(models.Model):
    document = models.FileField(
        upload_to=due_diligence_documents, storage=PrivateStorage()
    )
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.vendor.full_name + ' -> ' + self.document.name
