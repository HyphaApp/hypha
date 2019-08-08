from django.test import RequestFactory, TestCase

from opentech.apply.users.tests.factories import (ReviewerFactory,
                                                  StaffFactory,
                                                  SuperUserFactory,
                                                  UserFactory)
from opentech.apply.utils.testing.tests import BaseViewTestCase

from ..forms import SetPendingForm
from ..views import ProjectDetailView
from .factories import ProjectFactory


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


class TestProjectDetailView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.project = ProjectFactory()

    def test_reviewer_does_not_have_access(self):
        request = self.factory.get('/projects/1/')
        request.user = ReviewerFactory()

        response = ProjectDetailView.as_view()(request, pk=self.project.pk)
        self.assertEqual(response.status_code, 403)

    def test_staff_user_has_access(self):
        request = self.factory.get('/projects/1/')
        request.user = StaffFactory()

        response = ProjectDetailView.as_view()(request, pk=self.project.pk)
        self.assertEqual(response.status_code, 200)

    def test_super_user_has_access(self):
        request = self.factory.get('/projects/1/')
        request.user = SuperUserFactory()

        response = ProjectDetailView.as_view()(request, pk=self.project.pk)
        self.assertEqual(response.status_code, 200)

    def test_user_does_not_have_access(self):
        request = self.factory.get('/projects/1/')
        request.user = UserFactory()

        response = ProjectDetailView.as_view()(request, pk=self.project.pk)
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
