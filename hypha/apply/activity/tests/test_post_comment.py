"""Tests for the "mini" comment form endpoint used by object detail sidebars."""

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from hypha.apply.activity.models import APPLICANT, COMMENT, Activity
from hypha.apply.funds.models.submissions import ApplicationSubmission
from hypha.apply.projects.models.payment import Invoice
from hypha.apply.projects.models.project import INVOICING_AND_REPORTING
from hypha.apply.projects.tests.factories import (
    InvoiceFactory,
    ProjectFactory,
)
from hypha.apply.users.tests.factories import (
    ApplicantFactory,
    ContractingApproverFactory,
    ContractingFactory,
    StaffFactory,
)


class BasePostCommentTestCase(TestCase):
    def setUp(self):
        self.url = reverse("activity:post-comment")
        self.vendor = ApplicantFactory()
        self.project = ProjectFactory(status=INVOICING_AND_REPORTING, user=self.vendor)
        self.submission = self.project.submission
        self.invoice = InvoiceFactory(project=self.project)

        self.submission_ct = ContentType.objects.get_for_model(ApplicationSubmission).pk
        self.invoice_ct = ContentType.objects.get_for_model(Invoice).pk

    def params(self, **overrides):
        params = {
            "source_content_type": self.submission_ct,
            "source_object_id": self.submission.pk,
            "related_content_type": self.invoice_ct,
            "related_object_id": self.invoice.pk,
        }
        params.update(overrides)
        return params

    def post(self, message="a comment", visibility=APPLICANT, **overrides):
        return self.client.post(
            self.url,
            {**self.params(**overrides), "message": message, "visibility": visibility},
            secure=True,
        )


class TestPostCommentAccess(BasePostCommentTestCase):
    def test_staff_can_get_form_and_post(self):
        self.client.force_login(StaffFactory())

        response = self.client.get(self.url, self.params(), secure=True)
        self.assertEqual(response.status_code, 200)

        response = self.post()
        self.assertEqual(response.status_code, 204)
        self.assertIn("commentAdded", response.headers["HX-Trigger"])

        comment = Activity.comments.get(related_object_id=self.invoice.pk)
        self.assertEqual(comment.message, "a comment")
        self.assertEqual(comment.source, self.submission)
        self.assertEqual(comment.related_object, self.invoice)

    def test_contracting_can_post(self):
        """Contracting staff see the PF/SOW sidebar, so they must be able to use it"""
        self.client.force_login(ContractingFactory())
        self.assertEqual(self.post().status_code, 204)

    def test_contracting_approver_can_post(self):
        self.client.force_login(ContractingApproverFactory())
        self.assertEqual(self.post().status_code, 204)

    def test_project_vendor_can_post(self):
        self.client.force_login(self.vendor)
        self.assertEqual(self.post().status_code, 204)

    def test_unrelated_applicant_is_denied(self):
        self.client.force_login(ApplicantFactory())

        self.assertEqual(
            self.client.get(self.url, self.params(), secure=True).status_code, 403
        )
        self.assertEqual(self.post().status_code, 403)
        self.assertFalse(Activity.objects.filter(type=COMMENT).exists())

    def test_anonymous_is_redirected(self):
        self.assertEqual(self.post().status_code, 302)


class TestPostCommentValidation(BasePostCommentTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(StaffFactory())

    def test_empty_post_is_a_404_not_a_500(self):
        response = self.client.post(self.url, {}, secure=True)
        self.assertEqual(response.status_code, 404)

    def test_non_numeric_ids_are_a_404_not_a_500(self):
        self.assertEqual(self.post(source_content_type="not-an-int").status_code, 404)
        self.assertEqual(self.post(related_object_id="not-an-int").status_code, 404)

    def test_source_must_be_a_submission(self):
        self.assertEqual(
            self.post(source_content_type=self.invoice_ct).status_code, 404
        )

    def test_unknown_source_object_is_a_404(self):
        self.assertEqual(self.post(source_object_id=0).status_code, 404)

    def test_related_object_type_must_be_allowlisted(self):
        self.assertEqual(
            self.post(
                related_content_type=self.submission_ct,
                related_object_id=self.submission.pk,
            ).status_code,
            404,
        )

    def test_related_object_must_belong_to_the_submissions_project(self):
        other_invoice = InvoiceFactory()
        self.assertEqual(self.post(related_object_id=other_invoice.pk).status_code, 404)
        self.assertFalse(Activity.objects.filter(type=COMMENT).exists())

    def test_comment_without_a_related_object_is_accepted(self):
        response = self.post(related_content_type="", related_object_id="")
        self.assertEqual(response.status_code, 204)
        self.assertIsNone(
            Activity.comments.get(source_object_id=self.submission.pk).related_object
        )

    def test_blank_message_re_renders_the_form_with_errors(self):
        response = self.post(message="   ")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertFalse(Activity.objects.filter(type=COMMENT).exists())
