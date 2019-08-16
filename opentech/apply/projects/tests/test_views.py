from io import BytesIO

from django.test import TestCase

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
from ..models import CONTRACTING, IN_PROGRESS
from ..views import ContractsMixin
from .factories import (
    ContractFactory,
    DocumentCategoryFactory,
    PacketFileFactory,
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
    def test_all_signed_and_approved_contracts_appear(self):
        project = ProjectFactory()
        user = StaffFactory()
        ContractFactory(project=project, is_signed=True, approver=user)
        ContractFactory(project=project, is_signed=True, approver=user)
        ContractFactory(project=project, is_signed=True, approver=user)

        contracts = ContractsMixin().get_contracts(project)

        self.assertEqual(len(contracts), 3)

    def test_mixture_with_latest_signed_returns_no_unsigned(self):
        project = ProjectFactory()
        user = StaffFactory()
        ContractFactory(project=project, is_signed=True, approver=user)
        ContractFactory(project=project, is_signed=False)
        ContractFactory(project=project, is_signed=True, approver=user)

        contracts = ContractsMixin().get_contracts(project)

        self.assertEqual(len(contracts), 2)
        for contract in contracts:
            self.assertTrue(contract.is_signed)

    def test_no_contracts_returns_nothing(self):
        project = ProjectFactory()
        contracts = ContractsMixin().get_contracts(project)

        self.assertIsNone(contracts)

    def test_some_unsigned_and_unapproved(self):
        project = ProjectFactory()
        ContractFactory(project=project, is_signed=False)
        ContractFactory(project=project, is_signed=False)
        ContractFactory(project=project, is_signed=False)

        contracts = ContractsMixin().get_contracts(project)

        self.assertEqual(len(contracts), 1)

    def test_some_signed_and_unapproved(self):
        project = ProjectFactory()
        ContractFactory(project=project, is_signed=True)
        ContractFactory(project=project, is_signed=True)
        ContractFactory(project=project, is_signed=True)

        contracts = ContractsMixin().get_contracts(project)

        self.assertEqual(len(contracts), 3)

    def test_mixture_of_both_latest_unsigned_and_unapproved(self):
        project = ProjectFactory()
        user = StaffFactory()
        ContractFactory(project=project, is_signed=True)
        ContractFactory(project=project, is_signed=True, approver=user)
        ContractFactory(project=project, is_signed=False)
        ContractFactory(project=project, is_signed=True, approver=user)
        latest = ContractFactory(project=project, is_signed=False)

        contracts = ContractsMixin().get_contracts(project)

        self.assertEqual(len(contracts), 4)
        self.assertEqual(latest, contracts[0])
        self.assertFalse(contracts[0].is_signed)
        for contract in contracts[1:]:
            self.assertTrue(contract.is_signed)

    def test_mixture_of_both_latest_signed_and_unapproved(self):
        project = ProjectFactory()
        user = StaffFactory()
        ContractFactory(project=project, is_signed=True)
        ContractFactory(project=project, is_signed=True, approver=user)
        ContractFactory(project=project, is_signed=False)
        ContractFactory(project=project, is_signed=True, approver=user)
        latest = ContractFactory(project=project, is_signed=True)

        contracts = ContractsMixin().get_contracts(project)

        self.assertEqual(len(contracts), 4)
        self.assertEqual(latest, contracts[0])
        self.assertTrue(contracts[0].is_signed)
        for contract in contracts:
            self.assertTrue(contract.is_signed)

    def test_mixture_of_both_latest_signed_and_approved(self):
        project = ProjectFactory()
        user = StaffFactory()
        ContractFactory(project=project, is_signed=True)
        ContractFactory(project=project, is_signed=True, approver=user)
        ContractFactory(project=project, is_signed=False)
        ContractFactory(project=project, is_signed=True, approver=user)
        latest = ContractFactory(project=project, is_signed=True, approver=user)

        contracts = ContractsMixin().get_contracts(project)

        self.assertEqual(len(contracts), 4)
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
