from hypha.apply.projects.models.vendor import BankInformation
from django.views.generic import CreateView, TemplateView
from django.shortcuts import redirect
from django.urls import reverse
from django.shortcuts import get_object_or_404

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


class CreateVendorView(SessionWizardView):
    model = Vendor
    file_storage = PrivateStorage()
    form_list = [
        CreateVendorFormStep1,
        CreateVendorFormStep2,
        CreateVendorFormStep3,
        CreateVendorFormStep4,
        CreateVendorFormStep5,
        CreateVendorFormStep6,
    ]
    template_name = 'application_projects/vendor_form.html'

    def done(self, form_list, **kwargs):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        cleaned_data = self.get_all_cleaned_data()
        vendor = project.vendor
        intermediary_bank_information = BankInformation.objects.create(
            account_routing_number=cleaned_data['ib_account_routing_number'],
            account_number=cleaned_data['ib_account_number'],
            account_currency=cleaned_data['ib_account_currency'],
            branch_address=cleaned_data['ib_branch_address']
        )
        bank_information = BankInformation.objects.create(
            account_holder_name=cleaned_data['account_holder_name'],
            account_routing_number=cleaned_data['account_routing_number'],
            account_number=cleaned_data['account_number'],
            account_currency=cleaned_data['account_currency'],
            need_extra_info=cleaned_data['need_extra_info'],
            branch_address=cleaned_data['branch_address'],
            iba_info=intermediary_bank_information
        )
        vendor.bank_info = bank_information
        vendor.full_name = cleaned_data['name']
        vendor.contractor_name = cleaned_data['contractor_name']
        vendor.type = cleaned_data['type']
        vendor.required_to_pay_taxes = cleaned_data['required_to_pay_taxes']
        vendor.save()
        return redirect(reverse('/vendor/success/', args=[project.id]))

    def get_form_kwargs(self, step):
        kwargs = super(CreateVendorView, self).get_form_kwargs(step)
        kwargs['site'] = Site.find_for_request(self.request)
        return kwargs


class VendorFormSuccess(TemplateView):
    template_name = "application_projects/vendor_success.html"
