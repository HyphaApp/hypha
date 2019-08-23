from decimal import Decimal
from io import BytesIO

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
from django.urls import reverse

from opentech.apply.funds.tests.factories import LabSubmissionFactory
from opentech.apply.users.tests.factories import (
    ApplicantFactory,
    ApproverFactory,
    ReviewerFactory,
    StaffFactory,
    SuperUserFactory,
    UserFactory
)
from opentech.apply.utils.testing.tests import BaseViewTestCase

from ..forms import SetPendingForm
from ..models import CONTRACTING, IN_PROGRESS, PAID
from ..views import ContractsMixin, PaymentsMixin, ProjectDetailSimplifiedView
from .factories import (
    ContractFactory,
    DocumentCategoryFactory,
    PacketFileFactory,
    PaymentReceiptFactory,
    PaymentRequestFactory,
    ProjectFactory
)


class TestCreateApprovalView(BaseViewTestCase):
    base_view_name = 'detail'
    url_name = 'funds:projects:{}'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {'pk': instance.id}

    def test_creating_an_approval_happy_path(self):
        project = ProjectFactory()
        self.assertEqual(project.approvals.count(), 0)

        response = self.post_page(project, {'form-submitted-add_approval_form': '', 'by': self.user.id})
        self.assertEqual(response.status_code, 200)

        project.refresh_from_db()
        approval = project.approvals.first()

        self.assertEqual(project.approvals.count(), 1)
        self.assertFalse(project.is_locked)
        self.assertEqual(project.status, 'contracting')

        self.assertEqual(approval.project_id, project.pk)


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


class TestUserProjectDetailView(BaseProjectDetailTestCase):
    user_factory = UserFactory

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
        ContractFactory(project=project, is_signed=False, approver=None)

        contracts = self.DummyContractsView(project).get_context_data()['contracts']

        self.assertEqual(len(contracts), 1)

    def test_all_signed_and_unapproved_returns_latest(self):
        project = ProjectFactory()
        ContractFactory(project=project, is_signed=True, approver=None)
        ContractFactory(project=project, is_signed=True, approver=None)
        latest = ContractFactory(project=project, is_signed=True, approver=None)

        contracts = self.DummyContractsView(project).get_context_data()['contracts']

        self.assertEqual(len(contracts), 1)
        self.assertEqual(latest, contracts[0])
        self.assertTrue(contracts[0].is_signed)
        self.assertIsNone(contracts[0].approver)

    def test_mixture_of_both_latest_unsigned_and_unapproved(self):
        project = ProjectFactory()
        user = StaffFactory()
        ContractFactory(project=project, is_signed=True, approver=None)
        ContractFactory(project=project, is_signed=True, approver=user)
        ContractFactory(project=project, is_signed=False, approver=None)
        ContractFactory(project=project, is_signed=True, approver=user)
        latest = ContractFactory(project=project, is_signed=False, approver=None)

        contracts = self.DummyContractsView(project).get_context_data()['contracts']

        self.assertEqual(len(contracts), 3)
        self.assertEqual(latest, contracts[0])
        self.assertFalse(contracts[0].is_signed)
        for contract in contracts[1:]:
            self.assertTrue(contract.is_signed)

    def test_mixture_of_both_latest_signed_and_unapproved(self):
        project = ProjectFactory()
        user = StaffFactory()
        ContractFactory(project=project, is_signed=True, approver=None)
        ContractFactory(project=project, is_signed=True, approver=user)
        ContractFactory(project=project, is_signed=False, approver=None)
        ContractFactory(project=project, is_signed=True, approver=user)
        latest = ContractFactory(project=project, is_signed=True, approver=None)

        contracts = self.DummyContractsView(project).get_context_data()['contracts']

        self.assertEqual(len(contracts), 3)
        self.assertEqual(latest, contracts[0])
        self.assertTrue(contracts[0].is_signed)
        for contract in contracts:
            self.assertTrue(contract.is_signed)

    def test_mixture_of_both_latest_signed_and_approved(self):
        project = ProjectFactory()
        user = StaffFactory()
        ContractFactory(project=project, is_signed=True, approver=None)
        ContractFactory(project=project, is_signed=True, approver=user)
        ContractFactory(project=project, is_signed=False, approver=None)
        ContractFactory(project=project, is_signed=True, approver=user)
        latest = ContractFactory(project=project, is_signed=True, approver=user)

        contracts = self.DummyContractsView(project).get_context_data()['contracts']

        self.assertEqual(len(contracts), 3)
        self.assertEqual(latest, contracts[0])
        self.assertTrue(contracts[0].is_signed)
        for contract in contracts:
            self.assertTrue(contract.is_signed)


class TestApproveContractView(BaseViewTestCase):
    base_view_name = 'approve-contract'
    url_name = 'funds:projects:{}'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {'pk': instance.project.id, 'contract_pk': instance.id}

    def test_approve_unapproved_contract(self):
        project = ProjectFactory(status=CONTRACTING)
        contract = ContractFactory(project=project, is_signed=True)

        response = self.post_page(contract, {
            'form-submitted-approve_contract_form': '',
            'id': contract.id,
        })
        self.assertEqual(response.status_code, 200)

        contract.refresh_from_db()
        self.assertEqual(contract.approver, self.user)

        project.refresh_from_db()
        self.assertEqual(project.status, IN_PROGRESS)

    def test_approve_already_approved_contract(self):
        project = ProjectFactory(status=CONTRACTING)
        user = UserFactory()
        contract = ContractFactory(project=project, is_signed=True, approver=user)

        response = self.post_page(contract, {
            'form-submitted-approve_contract_form': '',
            'id': contract.id,
        })
        self.assertEqual(response.status_code, 200)

        contract.refresh_from_db()
        self.assertEqual(contract.approver, self.user)

        project.refresh_from_db()
        self.assertEqual(project.status, IN_PROGRESS)

    def test_approve_unsigned_contract(self):
        project = ProjectFactory()
        contract = ContractFactory(project=project, is_signed=False)

        response = self.post_page(contract, {
            'form-submitted-approve_contract_form': '',
            'id': contract.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.absolute_url(project.get_absolute_url()))

        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)


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
    base_view_name = 'detail'
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
            'value': '10',
            'date_from': '2018-08-15',
            'date_to': '2019-08-15',
            'comment': 'test comment',
            'invoice': invoice,
            'receipts': receipts,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(project.payment_requests.count(), 1)

        self.assertEqual(project.payment_requests.first().by, self.user)


class TestRequestPaymentViewAsStaff(BaseViewTestCase):
    base_view_name = 'detail'
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
            'value': '10',
            'date_from': '2018-08-15',
            'date_to': '2019-08-15',
            'comment': 'test comment',
            'invoice': invoice,
            'receipts': receipts,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(project.payment_requests.count(), 1)

        self.assertEqual(project.payment_requests.first().by, self.user)


class TestPaymentsMixin(TestCase):
    def test_get_totals(self):
        project = ProjectFactory(value=100)
        user = UserFactory()

        PaymentRequestFactory(project=project, by=user, value=20)
        PaymentRequestFactory(project=project, by=user, value=10, status=PAID)

        values = PaymentsMixin().get_totals(project)

        self.assertEqual(values['awaiting_absolute'], 20)
        self.assertEqual(values['awaiting_percentage'], 20)
        self.assertEqual(values['paid_absolute'], 10)
        self.assertEqual(values['paid_percentage'], 10)


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


class TestApplicantEditPaymentRequestView(BaseViewTestCase):
    base_view_name = 'edit-payment-request'
    url_name = 'funds:projects:{}'
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {'pk': instance.project.pk, 'payment_request_id': instance.pk}

    def test_editing_payment_request_fires_messaging(self):
        project = ProjectFactory(user=self.user)
        payment_request = PaymentRequestFactory(project=project)
        receipt = PaymentReceiptFactory(payment_request=payment_request)

        value = payment_request.value

        invoice = BytesIO(b'somebinarydata')
        invoice.name = 'invoice.pdf'

        response = self.post_page(payment_request, {
            'form-submitted-edit_request_payment_form': '',
            'value': value + 1,
            'date_from': '2018-08-15',
            'date_to': '2019-08-15',
            'comment': 'test comment',
            'invoice': invoice,
            'receipt_list': [receipt.pk],
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(project.payment_requests.count(), 1)

        payment_request.refresh_from_db()

        self.assertEqual(project.payment_requests.first().pk, payment_request.pk)

        self.assertEqual(value + Decimal("1"), payment_request.value)


class TestStaffEditPaymentRequestView(BaseViewTestCase):
    base_view_name = 'edit-payment-request'
    url_name = 'funds:projects:{}'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {'pk': instance.project.pk, 'payment_request_id': instance.pk}

    def test_editing_payment_request_fires_messaging(self):
        project = ProjectFactory()
        payment_request = PaymentRequestFactory(project=project)
        receipt = PaymentReceiptFactory(payment_request=payment_request)

        value = payment_request.value

        invoice = BytesIO(b'somebinarydata')
        invoice.name = 'invoice.pdf'

        response = self.post_page(payment_request, {
            'form-submitted-request_payment_form': '',
            'value': value + 1,
            'date_from': '2018-08-15',
            'date_to': '2019-08-15',
            'comment': 'test comment',
            'invoice': invoice,
            'receipt_list': [receipt.pk],
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(project.payment_requests.count(), 1)

        payment_request.refresh_from_db()

        self.assertEqual(project.payment_requests.first().pk, payment_request.pk)

        self.assertEqual(value + Decimal("1"), payment_request.value)
