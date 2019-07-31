from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase

from opentech.apply.users.tests.factories import (ReviewerFactory,
                                                  StaffFactory,
                                                  SuperUserFactory,
                                                  UserFactory)

from ..views import ProjectDetailView
from .factories import ProjectFactory


class TestProjectDetailView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.project = ProjectFactory()

    def test_reviewer_does_not_have_access(self):
        request = self.factory.get('/projects/1/')
        request.user = ReviewerFactory()

        with self.assertRaises(PermissionDenied):
            ProjectDetailView.as_view()(request, pk=self.project.pk)

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

        with self.assertRaises(PermissionDenied):
            ProjectDetailView.as_view()(request, pk=self.project.pk)
