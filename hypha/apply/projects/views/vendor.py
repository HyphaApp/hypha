from django.shortcuts import get_object_or_404, render

from wagtail.core.models import Site
from formtools.wizard.views import SessionWizardView
from hypha.apply.utils.storage import PrivateStorage

from ..models import Project, Vendor, DueDiligenceDocument, BankInformation
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


class CreateVendorView(SessionWizardView):
    model = Vendor
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

    def done(self, form_list, **kwargs):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        cleaned_data = self.get_all_cleaned_data()
        vendor = project.vendor
        vendor, _ = Vendor.objects.get_or_create(
            user=project.user
        )
        need_extra_info = cleaned_data['need_extra_info']
        bank_information = BankInformation.objects.create(
            account_holder_name=cleaned_data['account_holder_name'],
            account_routing_number=cleaned_data['account_routing_number'],
            account_number=cleaned_data['account_number'],
            account_currency=cleaned_data['account_currency'],
            need_extra_info=need_extra_info,
        )
        if need_extra_info:
            intermediary_bank_information = BankInformation.objects.create(
                account_routing_number=cleaned_data['ib_account_routing_number'],
                account_number=cleaned_data['ib_account_number'],
                account_currency=cleaned_data['ib_account_currency'],
                # branch_address=cleaned_data['ib_branch_address']
            )
            bank_information.branch_address = cleaned_data['branch_address']
            bank_information.iba_info = intermediary_bank_information
            bank_information.save()

        vendor.bank_info = bank_information
        vendor.full_name = cleaned_data['name']
        vendor.contractor_name = cleaned_data['contractor_name']
        vendor.type = cleaned_data['type']
        vendor.required_to_pay_taxes = cleaned_data['required_to_pay_taxes']
        vendor.save()
        for f in cleaned_data["due_diligence_documents"]:
            try:
                DueDiligenceDocument.objects.create(vendor=vendor, document=f)
            finally:
                f.close()
        form = self.get_form(step='documents')
        form.delete_temporary_files()
        return render(self.request, 'application_projects/vendor_success.html')

    def get_form_kwargs(self, step):
        kwargs = super(CreateVendorView, self).get_form_kwargs(step)
        kwargs['site'] = Site.find_for_request(self.request)
        return kwargs
