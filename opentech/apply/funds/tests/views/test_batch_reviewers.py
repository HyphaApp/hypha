from django.utils.text import slugify

from opentech.apply.funds.tests.factories import (
    ApplicationSubmissionFactory,
    AssignedWithRoleReviewersFactory,
    ReviewerRoleFactory,
)
from opentech.apply.users.tests.factories import (
    ReviewerFactory,
    StaffFactory,
)
from opentech.apply.review.tests.factories import ReviewFactory
from opentech.apply.utils.testing.tests import BaseViewTestCase


class BaseBatchReviewerTestCase(BaseViewTestCase):
    url_name = 'funds:submissions:{}'
    base_view_name = 'list'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.submissions = ApplicationSubmissionFactory.create_batch(4)
        cls.staff = StaffFactory.create_batch(4)
        cls.reviewers = ReviewerFactory.create_batch(4)
        cls.roles = ReviewerRoleFactory.create_batch(2)

    def data(self, reviewer_roles, submissions):
        data = {
            'form-submitted-batch_reviewer_form': 'Update',
            'submissions': ','.join([str(submission.id) for submission in submissions]),
        }

        data.update(
            **{
                f'role_reviewer_{slugify(str(role))}': reviewer.id
                for role, reviewer in zip(self.roles, reviewer_roles)
            }
        )
        return data


class StaffTestCase(BaseBatchReviewerTestCase):
    user_factory = StaffFactory

    def test_can_assign_role_reviewers(self):
        reviewer_roles = [self.staff[0]]
        submissions = self.submissions[0:2]
        self.post_page(data=self.data(reviewer_roles, submissions))
        for submission in submissions:
            self.assertEqual(submission.assigned.count(), 1)
            self.assertEqual(submission.assigned.first().reviewer, self.staff[0])
            self.assertEqual(submission.assigned.first().role, self.roles[0])

    def test_can_reassign_role_reviewers(self):
        AssignedWithRoleReviewersFactory(reviewer=self.staff[1], submission=self.submissions[0], role=self.roles[0])
        AssignedWithRoleReviewersFactory(reviewer=self.staff[1], submission=self.submissions[1], role=self.roles[0])
        submissions = self.submissions[0:2]
        reviewer_roles = [self.staff[0]]
        self.post_page(data=self.data(reviewer_roles, submissions))
        for submission in submissions:
            self.assertEqual(submission.assigned.count(), 1)
            self.assertEqual(submission.assigned.first().reviewer, self.staff[0])
            self.assertEqual(submission.assigned.first().role, self.roles[0])

    def test_can_reassign_from_other_role_reviewers(self):
        AssignedWithRoleReviewersFactory(reviewer=self.staff[0], submission=self.submissions[0], role=self.roles[1])
        AssignedWithRoleReviewersFactory(reviewer=self.staff[0], submission=self.submissions[1], role=self.roles[1])
        submissions = self.submissions[0:2]
        reviewer_roles = [self.staff[0]]
        self.post_page(data=self.data(reviewer_roles, submissions))
        for submission in submissions:
            self.assertEqual(submission.assigned.count(), 1)
            self.assertEqual(submission.assigned.first().reviewer, self.staff[0])
            self.assertEqual(submission.assigned.first().role, self.roles[0])

    def test_doesnt_remove_if_already_reviewed(self):
        AssignedWithRoleReviewersFactory(reviewer=self.staff[1], submission=self.submissions[0], role=self.roles[0])
        ReviewFactory(author__reviewer=self.staff[1], author__staff=True, submission=self.submissions[0], draft=False)
        ReviewFactory(author__reviewer=self.staff[1], author__staff=True, submission=self.submissions[1], draft=False)
        submissions = self.submissions[0:2]
        reviewer_roles = [self.staff[0]]
        self.post_page(data=self.data(reviewer_roles, submissions))
        for submission in submissions:
            self.assertEqual(submission.assigned.count(), 2)
            reviewers = submission.assigned.values_list('reviewer', flat=True)
            self.assertIn(self.staff[0].pk, reviewers)
            self.assertIn(self.staff[1].pk, reviewers)
