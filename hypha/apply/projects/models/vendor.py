from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.core.fields import RichTextField

from hypha.apply.utils.storage import PrivateStorage


class BankInformation(models.Model):
    account_holder_name = models.CharField(max_length=150)
    account_routing_number = models.CharField(max_length=10)
    account_number = models.CharField(max_length=20)
    account_currency = models.CharField(
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
        blank=True,
        verbose_name='National Identity Document Number'
    )

    def __str__(self):
        return self.account_holder_name


class Vendor(models.Model):

    TYPE_CHOICES = [
        ('organization', _('Yes, the account belongs to the organisation above')),
        ('personal', _('No, it is a personal bank account')),
    ]
    created_at = models.DateTimeField(verbose_name=_('Creation time'), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_('Update time'), auto_now=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='vendor'
    )
    name = models.CharField(max_length=150, blank=True)
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
    # tracks updates to the Vendor fields via the Vendor Setup Form.
    user_has_updated_details = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class DueDiligenceDocument(models.Model):
    document = models.FileField(
        upload_to="due_diligence_documents", storage=PrivateStorage()
    )
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='due_diligence_documents',
    )

    def __str__(self):
        return self.vendor.name + ' -> ' + self.document.name


@register_setting
class VendorFormSettings(BaseSetting):
    name_label = models.TextField(
        'label',
        default='1. What is the name of the person/organisation on the contract?'
    )
    name_help_text = RichTextField(
        'help text', blank=True,
        default='This is the party name in the contract.'
    )
    contractor_name_label = models.TextField(
        'label',
        default="2. What is the individual's name who is signing the contract?"
    )
    contractor_name_help_text = RichTextField(
        'help text', blank=True,
        default="This person is is authorised to sign contract on behalf of the person or organization named above."
    )
    type_label = models.TextField(
        'label',
        default='3. Is the bank account owned by the person or organisation in the Question 1 above?'
    )
    type_help_text = RichTextField(
        'help text',
        blank=True,
        default='The name of the bank account must be the same as on the contract.'
    )
    required_to_pay_taxes_label = models.TextField(
        'label',
        default='Is the organisation required to pay US taxes?'
    )
    required_to_pay_taxes_help_text = RichTextField(
        'help text',
        default='', blank=True,
    )
    due_diligence_documents_label = models.TextField(
        'label',
        default='Due Diligence Documents'
    )
    due_diligence_documents_help_text = RichTextField(
        'help text',
        blank=True,
        default='Upload Due Diligence Documents. E.g. w8/w9 forms.'
    )
    account_holder_name_label = models.TextField(
        'label',
        default='Bank Account Holder name'
    )
    account_holder_name_help_text = RichTextField(
        'help text',
        blank=True,
        default='This name must be same as the person or organisation that signed the contract. '
        'This person is authorised to sign contracts on behalf of the person or organisation named above.'
    )
    account_routing_number_label = models.TextField(
        'label',
        default='Bank Account Routing number'
    )
    account_routing_number_help_text = RichTextField(
        'help text',
        blank=True,
        default='Depending on your country, this might be called the ACH, SWIFT, BIC or ABA number.'
    )
    account_number_label = models.TextField(
        'label',
        default='Bank Account Number'
    )
    account_number_help_text = RichTextField(
        'help text',
        blank=True,
        default='Depending on your country, this might be called the account number, IBAN, or BBAN number.'
    )
    account_currency_label = models.TextField(
        'label',
        default='Bank Account Currency'
    )
    account_currency_help_text = RichTextField(
        'help text',
        blank=True,
        default='This is the currency of this bank account.'
    )
    need_extra_info_label = models.TextField(
        'label',
        default='Do you need to provide us with extra information?'
    )
    need_extra_info_help_text = RichTextField(
        'help text',
        blank=True,
        default=''
    )
    branch_address_label = models.TextField(
        'label',
        default='Bank Account Branch Address'
    )
    branch_address_help_text = models.TextField(
        'help text',
        blank=True,
        default='The address of the bank branch where you have the bank account '
        'located(not the bank account holder address)'
    )
    ib_account_routing_number_label = models.TextField(
        'label',
        default='Intermediary Bank Account Routing Number'
    )
    ib_account_routing_number_help_text = RichTextField(
        'help text',
        blank=True,
        default='Depending on your country, this might be called ACH, SWIFT, BIC or ABA number'
    )
    ib_account_number_label = models.TextField(
        'label',
        default='Intermediary Bank Account Number'
    )
    ib_account_number_help_text = RichTextField(
        'help text',
        blank=True,
        default='Depending on your country, this might be called the account number, IBAN, or BBAN number'
    )
    ib_account_currency_label = models.TextField(
        'label',
        default='Intermediary Bank Account Currency'
    )
    ib_account_currency_help_text = RichTextField(
        'help text',
        blank=True,
        default='This is the currency of this bank account'
    )
    ib_branch_address_label = models.TextField(
        'label',
        default='Intermediary Bank Branch Address'
    )
    ib_branch_address_help_text = RichTextField(
        'help text',
        blank=True,
        default='Bank branch address(not the bank account holder address)'
    )
    nid_type_label = models.TextField(
        'label',
        default='Account Holder National Identity Document Type'
    )
    nid_type_help_text = RichTextField(
        'help text',
        blank=True,
        default='This could be a passport, a National Identity number, '
        'or other national identity document.'
    )
    nid_number_label = models.TextField(
        'label',
        default='Account Holder National Identity Document Number'
    )
    nid_number_help_text = RichTextField(
        'help text',
        default='',
        blank=True,
    )
    other_info_label = models.TextField(
        'label',
        default='Other Information'
    )
    other_info_help_text = RichTextField(
        'help text',
        blank=True,
        default='If you need to include other information not listed above, provide it here.'
    )

    panels = [
        MultiFieldPanel([
            FieldPanel('name_label'),
            FieldPanel('name_help_text'),
        ], 'Name'),
        MultiFieldPanel([
            FieldPanel('contractor_name_label'),
            FieldPanel('contractor_name_help_text'),
        ], 'Contractor Name'),
        MultiFieldPanel([
            FieldPanel('type_label'),
            FieldPanel('type_help_text'),
        ], 'Type'),
        MultiFieldPanel([
            FieldPanel('required_to_pay_taxes_label'),
            FieldPanel('required_to_pay_taxes_help_text'),
        ], 'Required to pay taxes'),
        MultiFieldPanel([
            FieldPanel('due_diligence_documents_label'),
            FieldPanel('due_diligence_documents_help_text'),
        ], 'Due Diligence Documents'),
        MultiFieldPanel([
            FieldPanel('account_holder_name_label'),
            FieldPanel('account_holder_name_help_text'),
        ], 'Account Holder Name'),
        MultiFieldPanel([
            FieldPanel('account_routing_number_label'),
            FieldPanel('account_routing_number_help_text'),
        ], 'Account Routing Number'),
        MultiFieldPanel([
            FieldPanel('account_number_label'),
            FieldPanel('account_number_help_text'),
        ], 'Account Number'),
        MultiFieldPanel([
            FieldPanel('account_currency_label'),
            FieldPanel('account_currency_help_text'),
        ], 'Account Currency'),
        MultiFieldPanel([
            FieldPanel('need_extra_info_label'),
            FieldPanel('need_extra_info_help_text'),
        ], 'Need Extra Info'),
        MultiFieldPanel([
            FieldPanel('branch_address_label'),
            FieldPanel('branch_address_help_text'),
        ], 'Account Branch Address'),
        MultiFieldPanel([
            FieldPanel('ib_account_routing_number_label'),
            FieldPanel('ib_account_routing_number_help_text'),
        ], 'Intermediary Account Routing Number'),
        MultiFieldPanel([
            FieldPanel('ib_account_number_label'),
            FieldPanel('ib_account_number_help_text'),
        ], 'Intermediary Account Number'),
        MultiFieldPanel([
            FieldPanel('ib_account_currency_label'),
            FieldPanel('ib_account_currency_help_text'),
        ], 'Intermediary Account Currency'),
        MultiFieldPanel([
            FieldPanel('ib_branch_address_label'),
            FieldPanel('ib_branch_address_help_text'),
        ], 'Intermediary Account Branch Address'),
        MultiFieldPanel([
            FieldPanel('nid_type_label'),
            FieldPanel('nid_type_help_text'),
        ], 'National Identity Document Type'),
        MultiFieldPanel([
            FieldPanel('nid_number_label'),
            FieldPanel('nid_number_help_text'),
        ], 'National Identity Document Number'),
        MultiFieldPanel([
            FieldPanel('other_info_label'),
            FieldPanel('other_info_help_text'),
        ], 'Other Information'),
    ]
