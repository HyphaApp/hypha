import json
from django.shortcuts import get_object_or_404, render
from django.core.exceptions import PermissionDenied
from django.db.models.fields.files import FieldFile

from wagtail.core.models import Site
from formtools.wizard.views import SessionWizardView
from hypha.apply.utils.storage import PrivateStorage

from ..models import Project, DueDiligenceDocument, BankInformation
from ..forms import (
    CreateVendorFormStep1,
    CreateVendorFormStep2,
    CreateVendorFormStep3,
    CreateVendorFormStep4,
    CreateVendorFormStep5,
    CreateVendorFormStep6,
)


def show_extra_info_form(wizard):
    # try to get the cleaned data of step where we ask if extra info is needed
    cleaned_data = wizard.get_cleaned_data_for_step('extra') or {}
    # check if the field ``extra_info`` box was checked.
    return cleaned_data.get('need_extra_info', True)


class VendorAccessMixin:
    def dispatch(self, request, *args, **kwargs):
        is_admin = request.user.is_apply_staff
        is_owner = request.user == self.get_project().user
        if not (is_owner or is_admin):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


class CreateVendorView(VendorAccessMixin, SessionWizardView):
    file_storage = PrivateStorage()
    form_list = [
        ('basic', CreateVendorFormStep1),
        ('taxes', CreateVendorFormStep2),
        ('documents', CreateVendorFormStep3),
        ('bank', CreateVendorFormStep4),
        ('extra', CreateVendorFormStep5),
        ('other', CreateVendorFormStep6),
    ]
    condition_dict = {'other': show_extra_info_form}
    template_name = 'application_projects/vendor_form.html'

    def get_project(self):
        return get_object_or_404(Project, pk=self.kwargs['pk'])

    def done(self, form_list, **kwargs):
        vendor_project = self.get_project()
        cleaned_data = self.get_all_cleaned_data()
        vendor = vendor_project.vendor
        need_extra_info = cleaned_data['need_extra_info']
        bank_info = vendor.bank_info
        account_holder_name = cleaned_data['account_holder_name']
        account_routing_number = cleaned_data['account_routing_number']
        account_number = cleaned_data['account_number']
        account_currency = cleaned_data['account_currency']
        if not bank_info:
            bank_info = BankInformation.objects.create(
                account_holder_name=account_holder_name,
                account_number=account_number,
                account_routing_number=account_routing_number,
                account_currency=account_currency,
                need_extra_info=need_extra_info,
            )
        else:
            bank_info.account_holder_name = account_holder_name
            bank_info.account_number = account_number
            bank_info.account_currency = account_currency
            bank_info.need_extra_info = need_extra_info
        if need_extra_info:
            ib_account_routing_number = cleaned_data['ib_account_routing_number']
            ib_account_number = cleaned_data['ib_account_number']
            ib_account_currency = cleaned_data['ib_account_currency']
            # branch_address=cleaned_data['ib_branch_address']
            iba_info = bank_info.iba_info
            if not iba_info:
                iba_info = BankInformation.objects.create(
                    account_routing_number=ib_account_routing_number,
                    account_number=ib_account_number,
                    account_currency=ib_account_currency,
                )
            else:
                iba_info.account_routing_number = ib_account_routing_number
                iba_info.account_number = ib_account_number
                iba_info.account_currency = ib_account_currency

            bank_info.branch_address = cleaned_data['branch_address']
            bank_info.nid_type = cleaned_data['nid_type']
            bank_info.nid_number = cleaned_data['nid_number']
            bank_info.iba_info = iba_info
            vendor.other_info = cleaned_data['other_info']

        bank_info.save()

        vendor.bank_info = bank_info
        vendor.name = cleaned_data['name']
        vendor.contractor_name = cleaned_data['contractor_name']
        vendor.type = cleaned_data['type']
        vendor.required_to_pay_taxes = cleaned_data['required_to_pay_taxes']
        vendor.save()

        not_deleted_original_filenames = [
            file['name'] for file in json.loads(cleaned_data['due_diligence_documents-uploads'])
        ]
        for f in vendor.due_diligence_documents.all():
            if f.document.name not in not_deleted_original_filenames:
                f.document.delete()
                f.delete()

        for f in cleaned_data["due_diligence_documents"]:
            if not isinstance(f, FieldFile):
                try:
                    DueDiligenceDocument.objects.create(vendor=vendor, document=f)
                finally:
                    f.close()
        form = self.get_form('documents')
        form.delete_temporary_files()
        return render(self.request, 'application_projects/vendor_success.html')

    def get_form_initial(self, step):
        vendor_project = self.get_project()
        vendor = vendor_project.vendor
        initial_dict = self.initial_dict.get(step, {})
        if vendor:
            initial_dict['basic'] = {
                'name': vendor.name,
                'contractor_name': vendor.contractor_name,
                'type': vendor.type
            }
            initial_dict['taxes'] = {
                'required_to_pay_taxes': vendor.required_to_pay_taxes
            }
            initial_dict['documents'] = {
                'due_diligence_documents': [
                    f.document for f in vendor.due_diligence_documents.all()
                ]
            }
            bank_info = vendor.bank_info
            if bank_info:
                initial_dict['bank'] = {
                    'account_holder_name': bank_info.account_holder_name,
                    'account_routing_number': bank_info.account_routing_number,
                    'account_number': bank_info.account_number,
                    'account_currency': bank_info.account_currency,
                }
                initial_dict['extra'] = {
                    'need_extra_info': bank_info.need_extra_info
                }
                initial_dict['other'] = {
                    'branch_address': bank_info.branch_address,
                    'nid_type': bank_info.nid_type,
                    'nid_number': bank_info.nid_number,
                    'other_info': vendor.other_info,
                }
                iba_info = bank_info.iba_info
                if iba_info:
                    initial_dict['other']['ib_account_routing_number'] = iba_info.account_routing_number
                    initial_dict['other']['ib_account_number'] = iba_info.account_number
                    initial_dict['other']['ib_account_currency'] = iba_info.account_currency
                    initial_dict['other']['ib_branch_address'] = iba_info.branch_address
        return initial_dict.get(step, {})

    def get_form_kwargs(self, step):
        kwargs = super(CreateVendorView, self).get_form_kwargs(step)
        kwargs['site'] = Site.find_for_request(self.request)
        return kwargs
