import datetime
from operator import itemgetter

from babel.core import get_global
from babel.numbers import get_currency_name, get_territory_currencies
from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django_file_form.forms import FileFormMixin

from addressfield.fields import AddressField
from hypha.apply.stream_forms.fields import MultiFileField

from ..models.vendor import VendorFormSettings


def get_active_currencies():
    active_currencies = []
    territories = get_global('territory_currencies').keys()
    for territory in territories:
        currencies = get_territory_currencies(territory, datetime.date.today())
        if currencies:
            for currency in currencies:
                if currency not in active_currencies:
                    active_currencies.append(currencies[0])
    return active_currencies


class BaseVendorForm:
    def __init__(self, site=None, *args, **kwargs):
        if site:
            self.form_settings = VendorFormSettings.for_site(site)
        super().__init__(*args, **kwargs)

    def apply_form_settings(self, fields):
        for field in fields:
            try:
                self.fields[field].label = getattr(self.form_settings, f'{field}_label')
            except AttributeError:
                pass
            try:
                self.fields[field].help_text = getattr(self.form_settings, f'{field}_help_text')
            except AttributeError:
                pass
        return fields


class CreateVendorFormStep1(BaseVendorForm, forms.Form):
    TYPE_CHOICES = [
        ('organization', _('Yes, the account belongs to the organisation above')),
        ('personal', _('No, it is a personal bank account')),
    ]

    name = forms.CharField(required=True)
    contractor_name = forms.CharField(required=True)
    type = forms.ChoiceField(choices=TYPE_CHOICES, required=True, widget=forms.RadioSelect)

    def __init__(self, *args, **kwargs):
        super(CreateVendorFormStep1, self).__init__(*args, **kwargs)
        self.fields = self.apply_form_settings(self.fields)


class CreateVendorFormStep2(BaseVendorForm, forms.Form):
    required_to_pay_taxes = forms.TypedChoiceField(
        choices=((False, 'No'), (True, 'Yes')),
        coerce=lambda x: x == 'True',
        widget=forms.RadioSelect,
        required=True
    )

    def __init__(self, *args, **kwargs):
        super(CreateVendorFormStep2, self).__init__(*args, **kwargs)
        self.fields = self.apply_form_settings(self.fields)


class CreateVendorFormStep3(FileFormMixin, BaseVendorForm, forms.Form):
    due_diligence_documents = MultiFileField(required=True)

    def __init__(self, *args, **kwargs):
        super(CreateVendorFormStep3, self).__init__(*args, **kwargs)
        self.fields = self.apply_form_settings(self.fields)


class CreateVendorFormStep4(BaseVendorForm, forms.Form):
    CURRENCY_CHOICES = [
        (currency, f'{get_currency_name(currency, locale=settings.LANGUAGE_CODE)} - {currency}')
        for currency in get_active_currencies()
    ]

    account_holder_name = forms.CharField(required=True)
    account_routing_number = forms.CharField(required=True)
    account_number = forms.CharField(required=True)
    account_currency = forms.ChoiceField(
        choices=sorted(CURRENCY_CHOICES, key=itemgetter(1)),
        required=True,
        initial='USD'
    )

    def __init__(self, *args, **kwargs):
        super(CreateVendorFormStep4, self).__init__(*args, **kwargs)
        self.fields = self.apply_form_settings(self.fields)


class CreateVendorFormStep5(BaseVendorForm, forms.Form):
    need_extra_info = forms.TypedChoiceField(
        choices=((False, _('No')), (True, _('Yes'))),
        coerce=lambda x: x == 'True',
        widget=forms.RadioSelect,
        required=True
    )

    def __init__(self, *args, **kwargs):
        super(CreateVendorFormStep5, self).__init__(*args, **kwargs)
        self.fields = self.apply_form_settings(self.fields)


class CreateVendorFormStep6(BaseVendorForm, forms.Form):
    CURRENCY_CHOICES = [
        (currency, f'{get_currency_name(currency, locale=settings.LANGUAGE_CODE)} - {currency}')
        for currency in get_active_currencies()
    ]
    branch_address = AddressField()
    ib_account_routing_number = forms.CharField(required=False)
    ib_account_number = forms.CharField(required=False)
    ib_account_currency = forms.ChoiceField(
        choices=sorted(CURRENCY_CHOICES, key=itemgetter(1)),
        required=False,
        initial='USD'
    )
    ib_branch_address = AddressField()
    nid_type = forms.CharField(required=False)
    nid_number = forms.CharField(required=False)
    other_info = forms.CharField(required=False, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(CreateVendorFormStep6, self).__init__(*args, **kwargs)
        self.fields = self.apply_form_settings(self.fields)
