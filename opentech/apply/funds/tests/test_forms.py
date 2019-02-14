from django.test import TestCase
from opentech.apply.funds.tests.factories import (
    ApplicationSubmissionFactory,
    AssignedWithRoleReviewersFactory,
    AssignedReviewersFactory,
    InvitedToProposalFactory,
    ReviewerRoleFactory,
)
from opentech.apply.review.tests.factories import ReviewFactory
from opentech.apply.users.tests.factories import (
    ReviewerFactory,
    StaffFactory,
)


from opentech.apply.funds.forms import UpdateReviewersForm


class TestReviewerFormQueries(TestCase):
    def test_queries_init_and_render(self):
        user = StaffFactory()

        ReviewerRoleFactory.create_batch(3)

        StaffFactory.create_batch(3)
        ReviewerFactory.create_batch(3)

        submission = InvitedToProposalFactory(lead=user, workflow_stages=2)

        # Reviewers
        # Assigned Reviewers
        # Roles
        with self.assertNumQueries(3):
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

        AssignedWithRoleReviewersFactory(role=roles[0], submission=submission, reviewer=staff[0])
        AssignedWithRoleReviewersFactory(role=roles[1], submission=submission, reviewer=staff[1])

        data = {}
        for field, user in zip(form.fields, staff):
            if field.startswith('role'):
                data[field] = user.id
            else:
                data[field] = None

        form = UpdateReviewersForm(data, user=user, instance=submission)

        self.assertTrue(form.is_valid())

        # 1 - Submission
        # 8 - 1 per role (2 savepoint, 1 get, 1 update)
        # 1 - check - orphaned
        with self.assertNumQueries(10):
            form.save()

    def test_queries_reviewers_swap(self):
        user = StaffFactory()
        submission = InvitedToProposalFactory(lead=user)

        reviewers = ReviewerFactory.create_batch(4)

        AssignedReviewersFactory(submission=submission, reviewer=reviewers[0])
        AssignedReviewersFactory(submission=submission, reviewer=reviewers[1])

        data = {'reviewer_reviewers': [reviewer.id for reviewer in reviewers[2:]]}

        form = UpdateReviewersForm(data, user=user, instance=submission)

        self.assertTrue(form.is_valid())

        # 1 - Submission
        # 1 - Delete old
        # 1 - Cache existing
        # 1 - Add new
        # 1 - check - orphaned
        with self.assertNumQueries(5):
            form.save()

    def test_queries_existing_reviews(self):
        user = StaffFactory()
        submission = InvitedToProposalFactory(lead=user)

        reviewers = ReviewerFactory.create_batch(4)

        ReviewFactory(submission=submission, author=reviewers[0])
        ReviewFactory(submission=submission, author=reviewers[1])

        data = {'reviewer_reviewers': [reviewer.id for reviewer in reviewers[2:]]}

        form = UpdateReviewersForm(data, user=user, instance=submission)

        self.assertTrue(form.is_valid())

        # 1 - Submission
        # 1 - Delete old
        # 1 - Cache existing
        # 1 - Add new
        # 1 - check - orphaned
        with self.assertNumQueries(5):
            form.save()
