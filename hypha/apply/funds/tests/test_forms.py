from django.test import TestCase

from hypha.apply.funds.forms import InviteCoApplicantForm, UpdateReviewersForm
from hypha.apply.funds.models import CoApplicantInvite
from hypha.apply.funds.tests.factories import (
    ApplicationSubmissionFactory,
    AssignedReviewersFactory,
    AssignedWithRoleReviewersFactory,
    InvitedToProposalFactory,
    ReviewerRoleFactory,
)
from hypha.apply.review.tests.factories import ReviewFactory
from hypha.apply.users.tests.factories import ReviewerFactory, StaffFactory


class TestReviewerFormQueries(TestCase):
    def test_queries_init_and_render(self):
        user = StaffFactory()

        ReviewerRoleFactory.create_batch(3)

        StaffFactory.create_batch(3)
        ReviewerFactory.create_batch(3)

        submission = InvitedToProposalFactory(lead=user, workflow_stages=2)

        # Reviewers
        # Meta categories
        # Assigned Reviewers
        # Roles
        # Screening decision
        with self.assertNumQueries(5):
            form = UpdateReviewersForm(user=user, instance=submission)

        # 3 x Staff - 1 per Role
        # 1 x reviewers queryset
        # 1 x submission reviewers
        with self.assertNumQueries(5):
            form.as_p()

    def test_queries_roles_swap(self):
        user = StaffFactory()
        submission = ApplicationSubmissionFactory()

        staff = StaffFactory.create_batch(4)
        roles = ReviewerRoleFactory.create_batch(2)

        form = UpdateReviewersForm(user=user, instance=submission)

        AssignedWithRoleReviewersFactory(
            role=roles[0], submission=submission, reviewer=staff[0], staff=True
        )
        AssignedWithRoleReviewersFactory(
            role=roles[1], submission=submission, reviewer=staff[1], staff=True
        )

        data = {}
        for field, user in zip(form.fields, staff, strict=False):
            if field.startswith("role"):
                data[field] = user.id
            else:
                data[field] = None

        form = UpdateReviewersForm(data, user=user, instance=submission)

        self.assertTrue(form.is_valid())

        # 1 - Submission
        # 24 - 12 per role =
        #    1 - delete role no review
        #    1 - select review
        #    2 - cascades
        #    1 - update role with review
        #    1 - auth group
        #    2 - savepoint
        #    1 - get
        #    1 - update
        #    2 - release savepoint
        with self.assertNumQueries(25):
            form.save()

    def test_queries_reviewers_swap(self):
        user = StaffFactory()
        submission = InvitedToProposalFactory(lead=user)

        reviewers = ReviewerFactory.create_batch(4)

        AssignedReviewersFactory(submission=submission, reviewer=reviewers[0])
        AssignedReviewersFactory(submission=submission, reviewer=reviewers[1])

        data = {"reviewer_reviewers": [reviewer.id for reviewer in reviewers[2:]]}

        form = UpdateReviewersForm(data, user=user, instance=submission)

        self.assertTrue(form.is_valid())

        # 1 - Submission
        # 1 - Select Review
        # 2 - Cascade
        # 1 - Fetch data
        # 1 - Cache existing
        # 1 - auth group
        # 1 - Add new
        with self.assertNumQueries(8):
            form.save()

    def test_queries_existing_reviews(self):
        user = StaffFactory()
        submission = InvitedToProposalFactory(lead=user)

        reviewers = ReviewerFactory.create_batch(4)

        ReviewFactory(submission=submission, author__reviewer=reviewers[0])
        ReviewFactory(submission=submission, author__reviewer=reviewers[1])

        data = {"reviewer_reviewers": [reviewer.id for reviewer in reviewers[2:]]}

        form = UpdateReviewersForm(data, user=user, instance=submission)

        self.assertTrue(form.is_valid())

        # 1 - Submission
        # 1 - Delete old
        # 1 - Cache existing
        # 1 - Add new
        with self.assertNumQueries(5):
            form.save()


class TestInviteCoApplicantForm(TestCase):
    def setUp(self):
        self.submission = ApplicationSubmissionFactory(user__email="owner@example.com")

    def make_form(self, email):
        return InviteCoApplicantForm(
            data={"invited_user_email": email, "submission": self.submission.id},
            submission=self.submission,
        )

    def test_owner_in_other_case_is_rejected(self):
        form = self.make_form("Owner@Example.com")
        self.assertFalse(form.is_valid())
        self.assertIn("invited_user_email", form.errors)

    def test_already_invited_in_other_case_is_rejected(self):
        CoApplicantInvite.objects.create(
            submission=self.submission, invited_user_email="co@example.com"
        )
        form = self.make_form("CO@example.com")
        self.assertFalse(form.is_valid())
        self.assertIn("invited_user_email", form.errors)

    def test_new_address_is_accepted(self):
        CoApplicantInvite.objects.create(
            submission=self.submission, invited_user_email="co@example.com"
        )
        form = self.make_form("other@example.com")
        self.assertTrue(form.is_valid(), form.errors)
