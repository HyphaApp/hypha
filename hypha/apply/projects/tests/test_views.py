import json
from decimal import Decimal
from io import BytesIO

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from hypha.apply.funds.tests.factories import LabSubmissionFactory
from hypha.apply.users.tests.factories import (
    ApplicantFactory,
    ApproverFactory,
    FinanceFactory,
    ReviewerFactory,
    StaffFactory,
    SuperUserFactory,
    UserFactory,
)
from hypha.apply.utils.testing.tests import BaseViewTestCase

from ..files import get_files
from ..forms import SetPendingForm
from ..models.payment import CHANGES_REQUESTED, SUBMITTED
from ..models.project import COMMITTED, CONTRACTING, IN_PROGRESS
from ..views.project import ContractsMixin, ProjectDetailSimplifiedView
from .factories import (
    ContractFactory,
    DocumentCategoryFactory,
    InvoiceFactory,
    PacketFileFactory,
    ProjectFactory,
    ReportFactory,
    ReportVersionFactory,
    SupportingDocumentFactory,
)


class TestUpdateLeadView(BaseViewTestCase):
    base_view_name = 'detail'
    url_name = 'funds:projects:{}'
    user_factory = ApproverFactory

    def get_kwargs(self, instance):
        return {'pk': instance.id}

    def test_update_lead(self):
        project = ProjectFactory()

        new_lead = self.user_factory()
        response = self.post_page(project, {'form-submitted-lead_form': '', 'lead': new_lead.id})
        self.assertEqual(response.status_code, 200)

        project.refresh_from_db()
        self.assertEqual(project.lead, new_lead)

    def test_update_lead_from_none(self):
        project = ProjectFactory(lead=None)

        new_lead = self.user_factory()
        response = self.post_page(project, {'form-submitted-lead_form': '', 'lead': new_lead.id})
        self.assertEqual(response.status_code, 200)

        project.refresh_from_db()
        self.assertEqual(project.lead, new_lead)


class TestCreateApprovalView(BaseViewTestCase):
    base_view_name = 'detail'
    url_name = 'funds:projects:{}'
    user_factory = ApproverFactory

    def get_kwargs(self, instance):
        return {'pk': instance.id}

    def test_creating_an_approval_happy_path(self):
        project = ProjectFactory(in_approval=True)
        self.assertEqual(project.approvals.count(), 0)

        response = self.post_page(project, {'form-submitted-add_approval_form': '', 'by': self.user.id})
        self.assertEqual(response.status_code, 200)

        project.refresh_from_db()
        self.assertEqual(project.approvals.count(), 1)
        self.assertFalse(project.is_locked)
        self.assertEqual(project.status, 'contracting')

        approval = project.approvals.first()
        self.assertEqual(approval.project_id, project.pk)

    def test_creating_an_approval_other_approver(self):
        project = ProjectFactory(in_approval=True)
        self.assertEqual(project.approvals.count(), 0)

        other = self.user_factory()
        response = self.post_page(project, {'form-submitted-add_approval_form': '', 'by': other.id})
        self.assertEqual(response.status_code, 200)

        project.refresh_from_db()
        self.assertEqual(project.approvals.count(), 0)
        self.assertTrue(project.is_locked)


class BaseProjectDetailTestCase(BaseViewTestCase):
    url_name = 'funds:projects:{}'
    base_view_name = 'detail'

    def get_kwargs(self, instance):
        return {'pk': instance.id}


class TestStaffProjectDetailView(BaseProjectDetailTestCase):
    user_factory = StaffFactory

    def test_has_access(self):
        project = ProjectFactory()
        response = self.get_page(project)
        self.assertEqual(response.status_code, 200)

    def test_lab_project_renders(self):
        project = ProjectFactory(submission=LabSubmissionFactory())
        response = self.get_page(project)
        self.assertEqual(response.status_code, 200)


class TestFinanceProjectDetailView(BaseProjectDetailTestCase):
    user_factory = FinanceFactory

    def test_has_access(self):
        project = ProjectFactory()
        response = self.get_page(project)
        self.assertEqual(response.status_code, 200)

    def test_lab_project_renders(self):
        project = ProjectFactory(submission=LabSubmissionFactory())
        response = self.get_page(project)
        self.assertEqual(response.status_code, 200)


class TestUserProjectDetailView(BaseProjectDetailTestCase):
    user_factory = ApplicantFactory

    def test_doesnt_have_access(self):
        project = ProjectFactory()
        response = self.get_page(project)
        self.assertEqual(response.status_code, 403)

    def test_owner_has_access(self):
        project = ProjectFactory(user=self.user)
        response = self.get_page(project)
        self.assertEqual(response.status_code, 200)


class TestSuperUserProjectDetailView(BaseProjectDetailTestCase):
    user_factory = SuperUserFactory

    def test_has_access(self):
        project = ProjectFactory()
        response = self.get_page(project)
        self.assertEqual(response.status_code, 200)


class TestReviewerUserProjectDetailView(BaseProjectDetailTestCase):
    user_factory = ReviewerFactory

    def test_doesnt_have_access(self):
        project = ProjectFactory()
        response = self.get_page(project)
        self.assertEqual(response.status_code, 403)


class TestStaffProjectRejectView(BaseProjectDetailTestCase):
    user_factory = StaffFactory

    def test_cant_reject(self):
        project = ProjectFactory(in_approval=True)
        response = self.post_page(project, {
            'form-submitted-rejection_form': '',
            'comment': 'needs to change',
        })
        self.assertEqual(response.status_code, 403)
        project = self.refresh(project)
        self.assertEqual(project.status, COMMITTED)
        self.assertTrue(project.is_locked)


class TestApproverProjectRejectView(BaseProjectDetailTestCase):
    user_factory = ApproverFactory

    def test_can_reject(self):
        project = ProjectFactory(in_approval=True)
        response = self.post_page(project, {
            'form-submitted-rejection_form': '',
            'comment': 'needs to change',
        })
        self.assertEqual(response.status_code, 200)
        project = self.refresh(project)
        self.assertEqual(project.status, COMMITTED)
        self.assertFalse(project.is_locked)

    def test_cant_reject_no_comment(self):
        project = ProjectFactory(in_approval=True)
        response = self.post_page(project, {
            'form-submitted-rejection_form': '',
            'comment': '',
        })
        self.assertEqual(response.status_code, 200)
        project = self.refresh(project)
        self.assertEqual(project.status, COMMITTED)
        self.assertTrue(project.is_locked)


class TestUserProjectRejectView(BaseProjectDetailTestCase):
    user_factory = ApplicantFactory

    def test_cant_reject(self):
        project = ProjectFactory(in_approval=True, user=self.user)
        response = self.post_page(project, {
            'form-submitted-rejection_form': '',
            'comment': 'needs to change',
        })
        self.assertEqual(response.status_code, 200)
        project = self.refresh(project)
        self.assertEqual(project.status, COMMITTED)
        self.assertTrue(project.is_locked)


class TestRemoveDocumentView(BaseViewTestCase):
    base_view_name = 'detail'
    url_name = 'funds:projects:{}'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {'pk': instance.id}

    def test_remove_document(self):
        project = ProjectFactory()
        document = PacketFileFactory()

        response = self.post_page(project, {
            'form-submitted-remove_document_form': '',
            'id': document.id,
        })
        project.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(document.pk, project.packet_files.values_list('pk', flat=True))

    def test_remove_non_existent_document(self):
        response = self.post_page(ProjectFactory(), {
            'form-submitted-remove_document_form': '',
            'id': 1,
        })
        self.assertEqual(response.status_code, 200)


class TestSendForApprovalView(BaseViewTestCase):
    base_view_name = 'detail'
    url_name = 'funds:projects:{}'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {'pk': instance.id}

    def test_send_for_approval_fails_when_project_is_locked(self):
        project = ProjectFactory(is_locked=True)

        # The view doesn't have any custom changes when form validation fails
        # so check that directly.
        form = SetPendingForm(instance=project)
        self.assertFalse(form.is_valid())

    def test_send_for_approval_fails_when_project_is_not_in_committed_state(self):
        project = ProjectFactory(status='in_progress')

        # The view doesn't have any custom changes when form validation fails
        # so check that directly.
        form = SetPendingForm(instance=project)
        self.assertFalse(form.is_valid())

    def test_send_for_approval_happy_path(self):
        project = ProjectFactory(is_locked=False, status='committed')

        response = self.post_page(project, {'form-submitted-request_approval_form': ''})
        self.assertEqual(response.status_code, 200)

        project.refresh_from_db()

        self.assertTrue(project.is_locked)
        self.assertEqual(project.status, 'committed')


class TestApplicantUploadContractView(BaseViewTestCase):
    base_view_name = 'detail'
    url_name = 'funds:projects:{}'
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {'pk': instance.id}

    def test_owner_upload_contract(self):
        project = ProjectFactory(user=self.user)

        test_doc = BytesIO(b'somebinarydata')
        test_doc.name = 'contract.pdf'

        response = self.post_page(project, {
            'form-submitted-contract_form': '',
            'file': test_doc,
        })
        self.assertEqual(response.status_code, 200)

        project.refresh_from_db()

        self.assertEqual(project.contracts.count(), 1)
        self.assertTrue(project.contracts.first().is_signed)

    def test_non_owner_upload_contract(self):
        project = ProjectFactory()
        contract_count = project.contracts.count()

        test_doc = BytesIO(b'somebinarydata')
        test_doc.name = 'contract.pdf'

        response = self.post_page(project, {
            'form-submitted-contract_form': '',
            'file': test_doc,
        })
        self.assertEqual(response.status_code, 403)

        project.refresh_from_db()
        self.assertEqual(project.contracts.count(), contract_count)


class TestStaffUploadContractView(BaseViewTestCase):
    base_view_name = 'detail'
    url_name = 'funds:projects:{}'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {'pk': instance.id}

    def test_upload_contract(self):
        project = ProjectFactory()

        test_doc = BytesIO(b'somebinarydata')
        test_doc.name = 'contract.pdf'

        response = self.post_page(project, {
            'form-submitted-contract_form': '',
            'file': test_doc,
        })
        self.assertEqual(response.status_code, 200)

        project.refresh_from_db()

        self.assertEqual(project.contracts.count(), 1)
        self.assertFalse(project.contracts.first().is_signed)

    def test_upload_contract_with_signed_set_to_true(self):
        project = ProjectFactory()

        test_doc = BytesIO(b'somebinarydata')
        test_doc.name = 'contract.pdf'

        response = self.post_page(project, {
            'form-submitted-contract_form': '',
            'file': test_doc,
            'is_signed': True,
        })
        self.assertEqual(response.status_code, 200)

        project.refresh_from_db()

        self.assertEqual(project.contracts.count(), 1)
        self.assertTrue(project.contracts.first().is_signed)


class TestStaffSelectDocumentView(BaseViewTestCase):
    base_view_name = 'detail'
    url_name = 'funds:projects:{}'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {'pk': instance.id}

    def test_can_choose(self):
        category = DocumentCategoryFactory()
        project = ProjectFactory()

        files = get_files(project)

        response = self.post_page(project, {
            'form-submitted-select_document_form': '',
            'category': category.id,
            'document': files[0].url,
        })
        self.assertEqual(response.status_code, 200)

        project.refresh_from_db()

        self.assertEqual(project.packet_files.count(), 1)


class TestApplicantSelectDocumentView(BaseViewTestCase):
    base_view_name = 'detail'
    url_name = 'funds:projects:{}'
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {'pk': instance.id}

    def test_can_choose(self):
        category = DocumentCategoryFactory()
        project = ProjectFactory(user=self.user)

        files = get_files(project)

        response = self.post_page(project, {
            'form-submitted-select_document_form': '',
            'category': category.id,
            'document': files[0].url,
        })
        self.assertEqual(response.status_code, 200)

        project.refresh_from_db()

        self.assertEqual(project.packet_files.count(), 1)


class TestUploadDocumentView(BaseViewTestCase):
    base_view_name = 'detail'
    url_name = 'funds:projects:{}'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {'pk': instance.id}

    def test_upload_document(self):
        category = DocumentCategoryFactory()
        project = ProjectFactory()

        test_doc = BytesIO(b'somebinarydata')
        test_doc.name = 'document.pdf'

        response = self.post_page(project, {
            'form-submitted-document_form': '',
            'title': 'test document',
            'category': category.id,
            'document': test_doc,
        })
        self.assertEqual(response.status_code, 200)

        project.refresh_from_db()

        self.assertEqual(project.packet_files.count(), 1)


class BaseProjectEditTestCase(BaseViewTestCase):
    url_name = 'funds:projects:{}'
    base_view_name = 'edit'

    def get_kwargs(self, instance):
        return {'pk': instance.id}


class TestUserProjectEditView(BaseProjectEditTestCase):
    user_factory = UserFactory

    def test_does_not_have_access(self):
        project = ProjectFactory()
        response = self.get_page(project)

        self.assertEqual(response.status_code, 403)

    def test_owner_has_access(self):
        project = ProjectFactory(user=self.user)
        response = self.get_page(project)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [])

    def test_no_lead_redirects(self):
        project = ProjectFactory(user=self.user, lead=None)
        response = self.get_page(project)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.url(project, 'detail'))

    def test_locked_redirects(self):
        project = ProjectFactory(user=self.user, is_locked=True)
        response = self.get_page(project)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.url(project, 'detail'))


class TestStaffProjectEditView(BaseProjectEditTestCase):
    user_factory = StaffFactory

    def test_staff_user_has_access(self):
        project = ProjectFactory()
        response = self.get_page(project)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [])

    def test_no_lead_redirects(self):
        project = ProjectFactory(user=self.user, lead=None)
        response = self.get_page(project)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.url(project, 'detail'))

    def test_locked_redirects(self):
        project = ProjectFactory(user=self.user, is_locked=True)
        response = self.get_page(project)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.url(project, 'detail'))

    def test_no_paf_form_renders(self):
        project = ProjectFactory(
            submission__round__parent__approval_form=None,
            form_fields=None,
            form_data={},
        )
        response = self.get_page(project)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [])

    def test_pulls_paf_from_fund(self):
        project = ProjectFactory(form_fields=None, form_data={})
        response = self.get_page(project)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [])

    def test_edited_form_renders(self):
        project = ProjectFactory()
        response = self.get_page(project)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [])


class TestApproverProjectEditView(BaseProjectEditTestCase):
    user_factory = ApproverFactory

    def test_approver_has_access_locked(self):
        project = ProjectFactory(is_locked=True)
        response = self.get_page(project)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [])


class TestSuperProjectEditView(BaseProjectEditTestCase):
    user_factory = StaffFactory

    def test_has_access(self):
        project = ProjectFactory()
        response = self.get_page(project)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [])


class TestReviewerProjectEditView(BaseProjectEditTestCase):
    user_factory = ReviewerFactory

    def test_does_not_have_access(self):
        project = ProjectFactory()
        response = self.get_page(project)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.redirect_chain, [])


class TestContractsMixin(TestCase):
    class DummyView:
        def get_context_data(self):
            return {}

    class DummyContractsView(ContractsMixin, DummyView):
        def __init__(self, project):
            self.project = project

        def get_object(self):
            return self.project

    def test_all_signed_and_approved_contracts_appear(self):
        project = ProjectFactory()
        user = StaffFactory()
        ContractFactory(project=project, is_signed=True, approver=user)
        ContractFactory(project=project, is_signed=True, approver=user)
        ContractFactory(project=project, is_signed=True, approver=user)

        contracts = self.DummyContractsView(project).get_context_data()['contracts']

        self.assertEqual(len(contracts), 3)

    def test_mixture_with_latest_signed_returns_no_unsigned(self):
        project = ProjectFactory()
        user = StaffFactory()
        ContractFactory(project=project, is_signed=True, approver=user)
        ContractFactory(project=project, is_signed=False, approver=None)
        ContractFactory(project=project, is_signed=True, approver=user)

        contracts = self.DummyContractsView(project).get_context_data()['contracts']

        self.assertEqual(len(contracts), 2)
        for contract in contracts:
            self.assertTrue(contract.is_signed)

    def test_no_contracts_returns_nothing(self):
        project = ProjectFactory()
        contracts = self.DummyContractsView(project).get_context_data()['contracts']

        self.assertEqual(len(contracts), 0)

    def test_all_unsigned_and_unapproved_returns_only_latest(self):
        project = ProjectFactory()
        ContractFactory(project=project, is_signed=False, approver=None)
        ContractFactory(project=project, is_signed=False, approver=None)
        latest = ContractFactory(project=project, is_signed=False, approver=None)

        context = self.DummyContractsView(project).get_context_data()

        contracts = context['contracts']
        to_approve = context['contract_to_approve']
        to_sign = context['contract_to_sign']

        self.assertEqual(len(contracts), 0)
        self.assertEqual(latest, to_sign)
        self.assertIsNone(to_approve)

    def test_all_signed_and_unapproved_returns_latest(self):
        project = ProjectFactory()
        ContractFactory(project=project, is_signed=True, approver=None)
        ContractFactory(project=project, is_signed=True, approver=None)
        latest = ContractFactory(project=project, is_signed=True, approver=None)

        context = self.DummyContractsView(project).get_context_data()

        contracts = context['contracts']
        to_approve = context['contract_to_approve']
        to_sign = context['contract_to_sign']

        self.assertEqual(len(contracts), 0)
        self.assertEqual(latest, to_approve)
        self.assertIsNone(to_sign)

    def test_mixture_of_both_latest_unsigned_and_unapproved(self):
        project = ProjectFactory()
        user = StaffFactory()
        ContractFactory(project=project, is_signed=True, approver=None)
        ContractFactory(project=project, is_signed=True, approver=user)
        ContractFactory(project=project, is_signed=False, approver=None)
        ContractFactory(project=project, is_signed=True, approver=user)
        latest = ContractFactory(project=project, is_signed=False, approver=None)

        context = self.DummyContractsView(project).get_context_data()

        contracts = context['contracts']
        to_approve = context['contract_to_approve']
        to_sign = context['contract_to_sign']

        self.assertEqual(len(contracts), 2)
        self.assertEqual(latest, to_sign)
        self.assertIsNone(to_approve)

    def test_mixture_of_both_latest_signed_and_unapproved(self):
        project = ProjectFactory()
        user = StaffFactory()
        ContractFactory(project=project, is_signed=True, approver=None)
        ContractFactory(project=project, is_signed=True, approver=user)
        ContractFactory(project=project, is_signed=False, approver=None)
        ContractFactory(project=project, is_signed=True, approver=user)
        latest = ContractFactory(project=project, is_signed=True, approver=None)

        context = self.DummyContractsView(project).get_context_data()

        contracts = context['contracts']
        to_approve = context['contract_to_approve']
        to_sign = context['contract_to_sign']

        self.assertEqual(len(contracts), 2)
        self.assertEqual(latest, to_approve)
        self.assertIsNone(to_sign)

    def test_mixture_of_both_latest_signed_and_approved(self):
        project = ProjectFactory()
        user = StaffFactory()
        ContractFactory(project=project, is_signed=True, approver=None)
        ContractFactory(project=project, is_signed=True, approver=user)
        ContractFactory(project=project, is_signed=False, approver=None)
        ContractFactory(project=project, is_signed=True, approver=user)
        ContractFactory(project=project, is_signed=True, approver=user)

        context = self.DummyContractsView(project).get_context_data()

        contracts = context['contracts']
        to_approve = context['contract_to_approve']
        to_sign = context['contract_to_sign']

        self.assertEqual(len(contracts), 3)
        self.assertIsNone(to_approve)
        self.assertIsNone(to_sign)


class TestApproveContractView(BaseViewTestCase):
    base_view_name = 'detail'
    url_name = 'funds:projects:{}'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {'pk': instance.id}

    def test_approve_unapproved_contract(self):
        project = ProjectFactory(status=CONTRACTING)
        contract = ContractFactory(project=project, is_signed=True, approver=None)

        response = self.post_page(project, {
            'form-submitted-approve_contract_form': '',
            'id': contract.id,
        })
        self.assertEqual(response.status_code, 200)

        contract.refresh_from_db()
        self.assertEqual(contract.approver, self.user)

        project.refresh_from_db()
        self.assertEqual(project.status, IN_PROGRESS)

    def test_approve_already_approved_contract(self):
        project = ProjectFactory(status=IN_PROGRESS)
        user = StaffFactory()
        contract = ContractFactory(project=project, is_signed=True, approver=user)

        response = self.post_page(project, {
            'form-submitted-approve_contract_form': '',
            'id': contract.id,
        })
        self.assertEqual(response.status_code, 200)

        contract.refresh_from_db()
        self.assertEqual(contract.approver, user)

        project.refresh_from_db()
        self.assertEqual(project.status, IN_PROGRESS)

    def test_approve_unsigned_contract(self):
        project = ProjectFactory()
        contract = ContractFactory(project=project, is_signed=False, approver=None)

        response = self.post_page(project, {
            'form-submitted-approve_contract_form': '',
            'id': contract.id,
        })
        self.assertEqual(response.status_code, 200)

        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)

    def test_attempt_to_approve_non_latest(self):
        project = ProjectFactory()
        contract_attempt = ContractFactory(project=project, is_signed=True, approver=None)
        contract_meant = ContractFactory(project=project, is_signed=True, approver=None)

        response = self.post_page(project, {
            'form-submitted-approve_contract_form': '',
            'id': contract_attempt.id,
        })
        self.assertEqual(response.status_code, 200)

        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        contract_attempt.refresh_from_db()
        contract_meant.refresh_from_db()
        self.assertIsNone(contract_attempt.approver)
        self.assertIsNone(contract_meant.approver)


class BasePacketFileViewTestCase(BaseViewTestCase):
    url_name = 'funds:projects:{}'
    base_view_name = 'document'

    def get_kwargs(self, instance):
        return {
            'pk': instance.project.pk,
            'file_pk': instance.id,
        }


class TestStaffPacketView(BasePacketFileViewTestCase):
    user_factory = StaffFactory

    def test_staff_can_access(self):
        document = PacketFileFactory()
        response = self.get_page(document)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [])


class TestUserPacketView(BasePacketFileViewTestCase):
    user_factory = ApplicantFactory

    def test_owner_can_access(self):
        document = PacketFileFactory(project__user=self.user)
        response = self.get_page(document)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [])

    def test_user_can_not_access(self):
        document = PacketFileFactory()
        response = self.get_page(document)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.redirect_chain, [])


class TestAnonPacketView(BasePacketFileViewTestCase):
    user_factory = AnonymousUser

    def test_anonymous_can_not_access(self):
        document = PacketFileFactory()
        response = self.get_page(document)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 2)
        for path, _ in response.redirect_chain:
            self.assertIn(reverse('users_public:login'), path)


class TestRequestPaymentViewAsApplicant(BaseViewTestCase):
    base_view_name = 'request'
    url_name = 'funds:projects:{}'
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {'pk': instance.id}

    def test_creating_a_payment_request(self):
        project = ProjectFactory(user=self.user)
        self.assertEqual(project.payment_requests.count(), 0)

        invoice = BytesIO(b'somebinarydata')
        invoice.name = 'invoice.pdf'

        receipts = BytesIO(b'someotherbinarydata')
        receipts.name = 'receipts.pdf'

        response = self.post_page(project, {
            'form-submitted-request_payment_form': '',
            'requested_value': '10',
            'date_from': '2018-08-15',
            'date_to': '2019-08-15',
            'invoice': invoice,
            'receipts': receipts,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(project.payment_requests.count(), 1)

        self.assertEqual(project.payment_requests.first().by, self.user)


class TestRequestPaymentViewAsStaff(BaseViewTestCase):
    base_view_name = 'request'
    url_name = 'funds:projects:{}'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {'pk': instance.id}

    def test_creating_a_payment_request(self):
        project = ProjectFactory()
        self.assertEqual(project.payment_requests.count(), 0)

        invoice = BytesIO(b'somebinarydata')
        invoice.name = 'invoice.pdf'

        receipts = BytesIO(b'someotherbinarydata')
        receipts.name = 'receipts.pdf'

        response = self.post_page(project, {
            'form-submitted-request_payment_form': '',
            'requested_value': '10',
            'date_from': '2018-08-15',
            'date_to': '2019-08-15',
            'comment': 'test comment',
            'invoice': invoice,
            'receipts': receipts,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(project.payment_requests.count(), 1)

        self.assertEqual(project.payment_requests.first().by, self.user)


class TestProjectDetailSimplifiedView(TestCase):
    def test_staff_only(self):
        factory = RequestFactory()
        project = ProjectFactory()

        request = factory.get(f'/project/{project.pk}')
        request.user = StaffFactory()

        response = ProjectDetailSimplifiedView.as_view()(request, pk=project.pk)
        self.assertEqual(response.status_code, 200)

        request.user = ApplicantFactory()
        with self.assertRaises(PermissionDenied):
            ProjectDetailSimplifiedView.as_view()(request, pk=project.pk)


class TestStaffDetailInvoiceStatus(BaseViewTestCase):
    base_view_name = 'invoice-detail'
    url_name = 'funds:projects:{}'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {
            'invoice_pk': instance.pk,
        }

    def test_can(self):
        invoice = InvoiceFactory()
        response = self.get_page(invoice, url_kwargs={'pk': invoice.project.pk})
        self.assertEqual(response.status_code, 200)

    def test_wrong_project_cant(self):
        other_project = ProjectFactory()
        invoice = InvoiceFactory()
        response = self.get_page(invoice, url_kwargs={'pk': other_project.pk})
        self.assertEqual(response.status_code, 404)


class TestFinanceDetailInvoiceStatus(BaseViewTestCase):
    base_view_name = 'invoice-detail'
    url_name = 'funds:projects:{}'
    user_factory = FinanceFactory

    def get_kwargs(self, instance):
        return {
            'invoice_pk': instance.pk,
        }

    def test_can(self):
        invoice = InvoiceFactory()
        response = self.get_page(invoice, url_kwargs={'pk': invoice.project.pk})
        self.assertEqual(response.status_code, 200)

    def test_wrong_project_cant(self):
        other_project = ProjectFactory()
        invoice = InvoiceFactory()
        response = self.get_page(invoice, url_kwargs={'pk': other_project.pk})
        self.assertEqual(response.status_code, 404)


class TestApplicantDetailInvoiceStatus(BaseViewTestCase):
    base_view_name = 'invoice-detail'
    url_name = 'funds:projects:{}'
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {
            'pk': instance.project.pk,
            'invoice_pk': instance.pk,
        }

    def test_can(self):
        invoice = InvoiceFactory(project__user=self.user)
        response = self.get_page(invoice)
        self.assertEqual(response.status_code, 200)

    def test_other_cant(self):
        invoice = InvoiceFactory()
        response = self.get_page(invoice)
        self.assertEqual(response.status_code, 403)


class TestApplicantEditInvoiceView(BaseViewTestCase):
    base_view_name = 'invoice-edit'
    url_name = 'funds:projects:{}'
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {
            'pk': instance.project.pk,
            'invoice_pk': instance.pk,
        }

    def test_editing_invoice_remove_supporting_document(self):
        invoice = InvoiceFactory(project__user=self.user)
        SupportingDocumentFactory(invoice=invoice)

        self.assertTrue(invoice.supporting_documents.exists())

        response = self.post_page(invoice, {
            'amount': invoice.amount,
            'date_from': '2018-08-15',
            'date_to': '2019-08-15',
            'comment': 'test comment',
            'invoice': '',
            'supporting_documents-uploads': '[]',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(invoice.supporting_documents.exists())

    def test_editing_payment_keeps_receipts(self):
        project = ProjectFactory(user=self.user)
        invoice = InvoiceFactory(project=project)
        supporting_document = SupportingDocumentFactory(invoice=invoice)

        amount = invoice.amount

        response = self.post_page(invoice, {
            'amount': amount + 1,
            'date_from': '2018-08-15',
            'date_to': '2019-08-15',
            'comment': 'test comment',
            'invoice': '',
            'supporting_documents-uploads': json.dumps([{"name": supporting_document.document.name, "size": supporting_document.document.size, "type": "existing"}]),
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(project.invoices.count(), 1)

        invoice.refresh_from_db()

        self.assertEqual(project.invoices.first().pk, invoice.pk)

        self.assertEqual(amount + Decimal("1"), invoice.amount)
        self.assertEqual(invoice.supporting_documents.first().document, supporting_document.document)


class TestStaffEditInvoiceView(BaseViewTestCase):
    base_view_name = 'invoice-edit'
    url_name = 'funds:projects:{}'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {
            'pk': instance.project.pk,
            'invoice_pk': instance.pk,
        }

    def test_editing_invoice_remove_supporting_document(self):
        invoice = InvoiceFactory()
        SupportingDocumentFactory(invoice=invoice)

        response = self.post_page(invoice, {
            'amount': invoice.amount,
            'date_from': '2018-08-15',
            'date_to': '2019-08-15',
            'comment': 'test comment',
            'invoice': '',
            'supporting_documents-uploads': '[]',
        })

        self.assertEqual(response.status_code, 200)

        self.assertFalse(invoice.supporting_documents.exists())

    def test_editing_invoice_keeps_supprting_document(self):
        project = ProjectFactory()
        invoice = InvoiceFactory(project=project)
        supporting_document = SupportingDocumentFactory(invoice=invoice)

        amount = invoice.amount

        document = BytesIO(b'somebinarydata')
        document.name = 'invoice.pdf'

        response = self.post_page(invoice, {
            'amount': amount + 1,
            'date_from': '2018-08-15',
            'date_to': '2019-08-15',
            'comment': 'test comment',
            'document': document,
            'supporting_documents-uploads': json.dumps([{"name": supporting_document.document.name, "size": supporting_document.document.size, "type": "existing"}]),
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(project.invoices.count(), 1)

        invoice.refresh_from_db()

        self.assertEqual(project.invoices.first().pk, invoice.pk)

        self.assertEqual(amount + Decimal("1"), invoice.amount)
        self.assertEqual(invoice.supporting_documents.first().document, supporting_document.document)


class TestStaffChangeInvoiceStatus(BaseViewTestCase):
    base_view_name = 'invoice-detail'
    url_name = 'funds:projects:{}'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {
            'pk': instance.project.pk,
            'invoice_pk': instance.pk,
        }

    def test_can(self):
        invoice = InvoiceFactory()
        response = self.post_page(invoice, {
            'form-submitted-change_invoice_status': '',
            'status': CHANGES_REQUESTED,
            'comment': 'this is a comment',
        })
        self.assertEqual(response.status_code, 200)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, CHANGES_REQUESTED)


class TestApplicantChangeInoviceStatus(BaseViewTestCase):
    base_view_name = 'invoice-detail'
    url_name = 'funds:projects:{}'
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {
            'pk': instance.project.pk,
            'invoice_pk': instance.pk,
        }

    def test_can(self):
        invoice = InvoiceFactory(project__user=self.user)
        response = self.post_page(invoice, {
            'form-submitted-change_invoice_status': '',
            'status': CHANGES_REQUESTED,
        })
        self.assertEqual(response.status_code, 200)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, SUBMITTED)

    def test_other_cant(self):
        invoice = InvoiceFactory()
        response = self.post_page(invoice, {
            'form-submitted-change_invoice_status': '',
            'status': CHANGES_REQUESTED,
        })
        self.assertEqual(response.status_code, 403)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, SUBMITTED)


class TestStaffInoviceDocumentPrivateMedia(BaseViewTestCase):
    base_view_name = 'invoice-document'
    url_name = 'funds:projects:{}'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {
            'invoice_pk': instance.pk,
        }

    def test_can_access(self):
        invoice = InvoiceFactory()
        response = self.get_page(invoice, url_kwargs={'pk': invoice.project.pk})
        self.assertContains(response, invoice.document.read())

    def test_cant_access_if_project_wrong(self):
        other_project = ProjectFactory()
        invoice = InvoiceFactory()
        response = self.get_page(invoice, url_kwargs={'pk': other_project.pk})
        self.assertEqual(response.status_code, 404)


class TestApplicantInvoiceDocumentPrivateMedia(BaseViewTestCase):
    base_view_name = 'invoice-document'
    url_name = 'funds:projects:{}'
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {
            'pk': instance.project.pk,
            'invoice_pk': instance.pk,
        }

    def test_can_access_own(self):
        invoice = InvoiceFactory(project__user=self.user)
        response = self.get_page(invoice)
        self.assertContains(response, invoice.document.read())

    def test_cant_access_other(self):
        invoice = InvoiceFactory()
        response = self.get_page(invoice)
        self.assertEqual(response.status_code, 403)


class TestStaffInvoiceSupportingDocumentPrivateMedia(BaseViewTestCase):
    base_view_name = 'invoice-supporting-document'
    url_name = 'funds:projects:{}'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {
            'pk': instance.invoice.project.pk,
            'invoice_pk': instance.invoice.pk,
            'file_pk': instance.pk,
        }

    def test_can_access(self):
        supporting_document = SupportingDocumentFactory()
        response = self.get_page(supporting_document)
        self.assertContains(response, supporting_document.document.read())


class TestApplicantSupportingDocumentPrivateMedia(BaseViewTestCase):
    base_view_name = 'invoice-supporting-document'
    url_name = 'funds:projects:{}'
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {
            'pk': instance.invoice.project.pk,
            'invoice_pk': instance.invoice.pk,
            'file_pk': instance.pk,
        }

    def test_can_access_own(self):
        supporting_document = SupportingDocumentFactory(invoice__project__user=self.user)
        response = self.get_page(supporting_document)
        self.assertContains(response, supporting_document.document.read())

    def test_cant_access_other(self):
        supporting_document = SupportingDocumentFactory()
        response = self.get_page(supporting_document)
        self.assertEqual(response.status_code, 403)


@override_settings(ROOT_URLCONF='hypha.apply.urls')
class TestProjectListView(TestCase):
    def test_staff_can_access_project_list_page(self):
        ProjectFactory(status=CONTRACTING)
        ProjectFactory(status=IN_PROGRESS)

        self.client.force_login(StaffFactory())

        url = reverse('apply:projects:all')

        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_applicants_cannot_access_project_list_page(self):
        ProjectFactory(status=CONTRACTING)
        ProjectFactory(status=IN_PROGRESS)

        self.client.force_login(UserFactory())

        url = reverse('apply:projects:all')

        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 403)


@override_settings(ROOT_URLCONF='hypha.apply.urls')
class TestProjectOverviewView(TestCase):
    def test_staff_can_access(self):
        ProjectFactory(status=CONTRACTING)
        ProjectFactory(status=IN_PROGRESS)

        self.client.force_login(StaffFactory())

        url = reverse('apply:projects:overview')

        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_applicants_cannot_access(self):
        ProjectFactory(status=CONTRACTING)
        ProjectFactory(status=IN_PROGRESS)

        self.client.force_login(UserFactory())

        url = reverse('apply:projects:overview')

        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 403)


class TestStaffSubmitReport(BaseViewTestCase):
    base_view_name = 'edit'
    url_name = 'funds:projects:reports:{}'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {
            'pk': instance.pk,
        }

    def test_get_page(self):
        report = ReportFactory()
        response = self.get_page(report)
        self.assertContains(response, report.project.title)

    def test_submit_report(self):
        report = ReportFactory()
        response = self.post_page(report, {'public_content': 'Some text'})
        report.refresh_from_db()
        self.assertRedirects(response, self.absolute_url(report.project.get_absolute_url()))
        self.assertEqual(report.versions.first().public_content, 'Some text')
        self.assertEqual(report.versions.first(), report.current)
        self.assertEqual(report.current.author, self.user)
        self.assertIsNone(report.draft)

    def test_submit_private_report(self):
        report = ReportFactory()
        response = self.post_page(report, {'private_content': 'Some text'})
        report.refresh_from_db()
        self.assertRedirects(response, self.absolute_url(report.project.get_absolute_url()))
        self.assertEqual(report.versions.first().private_content, 'Some text')
        self.assertEqual(report.versions.first(), report.current)
        self.assertEqual(report.current.author, self.user)
        self.assertIsNone(report.draft)

    def test_cant_submit_blank_report(self):
        report = ReportFactory()
        response = self.post_page(report, {})
        report.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(report.versions.count(), 0)

    def test_save_report_draft(self):
        report = ReportFactory()
        response = self.post_page(report, {'public_content': 'Some text', 'save': 'Save'})
        report.refresh_from_db()
        self.assertRedirects(response, self.absolute_url(report.project.get_absolute_url()))
        self.assertEqual(report.versions.first().public_content, 'Some text')
        self.assertEqual(report.versions.first(), report.draft)
        self.assertIsNone(report.current)

    def test_save_report_with_draft(self):
        report = ReportFactory(is_draft=True)
        self.assertEqual(report.versions.first(), report.draft)
        response = self.post_page(report, {'public_content': 'Some text'})
        report.refresh_from_db()
        self.assertRedirects(response, self.absolute_url(report.project.get_absolute_url()))
        self.assertEqual(report.versions.last().public_content, 'Some text')
        self.assertEqual(report.versions.last(), report.current)
        self.assertIsNone(report.draft)

    def test_edit_submitted_report(self):
        report = ReportFactory(is_submitted=True)
        self.assertEqual(report.versions.first(), report.current)
        response = self.post_page(report, {'public_content': 'Some text', 'save': ' Save'})
        report.refresh_from_db()
        self.assertRedirects(response, self.absolute_url(report.project.get_absolute_url()))
        self.assertEqual(report.versions.last().public_content, 'Some text')
        self.assertEqual(report.versions.last(), report.draft)
        self.assertEqual(report.versions.first(), report.current)

    def test_resubmit_submitted_report(self):
        yesterday = timezone.now() - relativedelta(days=1)
        version = ReportVersionFactory(submitted=yesterday)
        report = version.report
        report.current = version
        report.submitted = version.submitted
        report.save()
        self.assertEqual(report.submitted, yesterday)
        self.assertEqual(report.versions.first(), report.current)
        response = self.post_page(report, {'public_content': 'Some text'})
        report.refresh_from_db()
        self.assertRedirects(response, self.absolute_url(report.project.get_absolute_url()))
        self.assertEqual(report.versions.last().public_content, 'Some text')
        self.assertEqual(report.versions.last(), report.current)
        self.assertIsNone(report.draft)
        self.assertEqual(report.submitted.date(), yesterday.date())
        self.assertEqual(report.current.submitted.date(), timezone.now().date())

    def test_cant_submit_future_report(self):
        submitted_report = ReportFactory(
            end_date=timezone.now() + relativedelta(days=1),
            is_submitted=True,
        )
        future_report = ReportFactory(
            end_date=timezone.now() + relativedelta(days=3),
            project=submitted_report.project,
        )
        response = self.post_page(future_report, {'public_content': 'Some text'})
        self.assertEqual(response.status_code, 403)


class TestApplicantSubmitReport(BaseViewTestCase):
    base_view_name = 'edit'
    url_name = 'funds:projects:reports:{}'
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {
            'pk': instance.pk,
        }

    def test_get_own_report(self):
        report = ReportFactory(project__user=self.user)
        response = self.get_page(report)
        self.assertContains(response, report.project.title)

    def test_cant_get_other_report(self):
        report = ReportFactory()
        response = self.get_page(report)
        self.assertEqual(response.status_code, 403)

    def test_submit_own_report(self):
        report = ReportFactory(project__user=self.user)
        response = self.post_page(report, {'public_content': 'Some text'})
        report.refresh_from_db()
        self.assertRedirects(response, self.absolute_url(report.project.get_absolute_url()))
        self.assertEqual(report.versions.first().public_content, 'Some text')
        self.assertEqual(report.versions.first(), report.current)
        self.assertEqual(report.current.author, self.user)

    def test_submit_private_report(self):
        report = ReportFactory(project__user=self.user)
        response = self.post_page(report, {'private_content': 'Some text'})
        report.refresh_from_db()
        self.assertRedirects(response, self.absolute_url(report.project.get_absolute_url()))
        self.assertEqual(report.versions.first().private_content, 'Some text')
        self.assertEqual(report.versions.first(), report.current)
        self.assertEqual(report.current.author, self.user)
        self.assertIsNone(report.draft)

    def test_cant_submit_blank_report(self):
        report = ReportFactory(project__user=self.user)
        response = self.post_page(report, {})
        report.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(report.versions.count(), 0)

    def test_save_report_draft(self):
        report = ReportFactory(project__user=self.user)
        response = self.post_page(report, {'public_content': 'Some text', 'save': 'Save'})
        report.refresh_from_db()
        self.assertRedirects(response, self.absolute_url(report.project.get_absolute_url()))
        self.assertEqual(report.versions.first().public_content, 'Some text')
        self.assertEqual(report.versions.first(), report.draft)
        self.assertIsNone(report.current)

    def test_save_report_with_draft(self):
        report = ReportFactory(is_draft=True, project__user=self.user)
        self.assertEqual(report.versions.first(), report.draft)
        response = self.post_page(report, {'public_content': 'Some text'})
        report.refresh_from_db()
        self.assertRedirects(response, self.absolute_url(report.project.get_absolute_url()))
        self.assertEqual(report.versions.last().public_content, 'Some text')
        self.assertEqual(report.versions.last(), report.current)
        self.assertIsNone(report.draft)

    def test_cant_edit_submitted_report(self):
        report = ReportFactory(is_submitted=True, project__user=self.user)
        self.assertEqual(report.versions.first(), report.current)
        response = self.post_page(report, {'public_content': 'Some text', 'save': ' Save'})
        self.assertEqual(response.status_code, 403)

    def test_cant_submit_other_report(self):
        report = ReportFactory()
        response = self.post_page(report, {'public_content': 'Some text'})
        self.assertEqual(response.status_code, 403)


class TestStaffReportDetail(BaseViewTestCase):
    base_view_name = 'detail'
    url_name = 'funds:projects:reports:{}'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {
            'pk': instance.pk,
        }

    def test_can_access_submitted_report(self):
        report = ReportFactory(is_submitted=True)
        response = self.get_page(report)
        self.assertEqual(response.status_code, 200)

    def test_cant_access_skipped_report(self):
        report = ReportFactory(skipped=True)
        response = self.get_page(report)
        self.assertEqual(response.status_code, 403)

    def test_cant_access_draft_report(self):
        report = ReportFactory(is_draft=True)
        response = self.get_page(report)
        self.assertEqual(response.status_code, 403)

    def test_cant_access_future_report(self):
        report = ReportFactory(end_date=timezone.now() + relativedelta(days=1))
        response = self.get_page(report)
        self.assertEqual(response.status_code, 403)


class TestApplicantReportDetail(BaseViewTestCase):
    base_view_name = 'detail'
    url_name = 'funds:projects:reports:{}'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {
            'pk': instance.pk,
        }

    def test_can_access_own_submitted_report(self):
        report = ReportFactory(is_submitted=True, project__user=self.user)
        response = self.get_page(report)
        self.assertEqual(response.status_code, 200)

    def test_cant_access_own_draft_report(self):
        report = ReportFactory(is_draft=True, project__user=self.user)
        response = self.get_page(report)
        self.assertEqual(response.status_code, 403)

    def test_cant_access_own_future_report(self):
        report = ReportFactory(end_date=timezone.now() + relativedelta(days=1), project__user=self.user)
        response = self.get_page(report)
        self.assertEqual(response.status_code, 403)

    def test_cant_access_other_submitted_report(self):
        report = ReportFactory(is_submitted=True)
        response = self.get_page(report)
        self.assertEqual(response.status_code, 200)

    def test_cant_access_other_draft_report(self):
        report = ReportFactory(is_draft=True)
        response = self.get_page(report)
        self.assertEqual(response.status_code, 403)

    def test_cant_access_other_future_report(self):
        report = ReportFactory(end_date=timezone.now() + relativedelta(days=1))
        response = self.get_page(report)
        self.assertEqual(response.status_code, 403)


class TestSkipReport(BaseViewTestCase):
    base_view_name = 'skip'
    url_name = 'funds:projects:reports:{}'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {
            'pk': instance.pk,
        }

    def test_can_skip_report(self):
        report = ReportFactory(past_due=True)
        response = self.post_page(report)
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        self.assertTrue(report.skipped)

    def test_can_unskip_report(self):
        report = ReportFactory(skipped=True, past_due=True)
        response = self.post_page(report)
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        self.assertFalse(report.skipped)

    def test_cant_skip_current_report(self):
        report = ReportFactory(end_date=timezone.now() + relativedelta(days=1))
        response = self.post_page(report)
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        self.assertFalse(report.skipped)

    def test_cant_skip_submitted_report(self):
        report = ReportFactory(is_submitted=True)
        response = self.post_page(report, data={})
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        self.assertFalse(report.skipped)

    def test_can_skip_draft_report(self):
        report = ReportFactory(is_draft=True, past_due=True)
        response = self.post_page(report)
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        self.assertTrue(report.skipped)


class TestStaffProjectPDFExport(BaseViewTestCase):
    base_view_name = 'download'
    url_name = 'funds:projects:{}'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {
            'pk': instance.pk,
        }

    def test_can_access(self):
        project = ProjectFactory()
        response = self.get_page(project)
        self.assertEqual(response.status_code, 200)

    def test_reponse_object_is_pdf(self):
        project = ProjectFactory()
        response = self.get_page(project)
        self.assertEqual(response.filename, project.title + '.pdf')


class ApplicantStaffProjectPDFExport(BaseViewTestCase):
    base_view_name = 'download'
    url_name = 'funds:projects:{}'
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {
            'pk': instance.pk,
        }

    def test_cant_access(self):
        project = ProjectFactory()
        response = self.get_page(project)
        self.assertEqual(response.status_code, 403)
