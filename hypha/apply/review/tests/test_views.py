from django.urls import reverse

from hypha.apply.activity.models import Activity
from hypha.apply.funds.models import ApplicationSubmission
from hypha.apply.funds.tests.factories.models import (
    ApplicationSubmissionFactory,
    AssignedReviewersFactory,
)
from hypha.apply.funds.workflows import INITIAL_STATE
from hypha.apply.users.tests.factories import ReviewerFactory, StaffFactory, UserFactory
from hypha.apply.utils.testing.tests import BaseViewTestCase

from ..models import Review, ReviewOpinion
from ..options import AGREE, DISAGREE, NA
from ..views import get_fields_for_stage
from .factories import (
    ReviewFactory,
    ReviewFormFactory,
    ReviewFormFieldsFactory,
    ReviewOpinionFactory,
)


class StaffReviewsTestCase(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = "funds:submissions:reviews:{}"
    base_view_name = "review"

    def get_kwargs(self, instance):
        return {"pk": instance.id, "submission_pk": instance.submission.id}

    def test_can_access_review(self):
        review = ReviewFactory(author__reviewer=self.user, author__staff=True)
        response = self.get_page(review)
        self.assertContains(response, review.submission.title)
        self.assertContains(response, self.user.full_name)
        self.assertContains(
            response,
            reverse("funds:submissions:detail", kwargs={"pk": review.submission.id}),
        )

    def test_can_access_other_review(self):
        submission = ApplicationSubmissionFactory()
        review = ReviewFactory(submission=submission)
        response = self.get_page(review)
        self.assertEqual(response.status_code, 200)


class StaffReviewListingTestCase(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = "funds:submissions:reviews:{}"
    base_view_name = "review"

    def get_kwargs(self, instance):
        return {"submission_pk": instance.id}

    def test_can_access_review_listing(self):
        submission = ApplicationSubmissionFactory()
        reviews = ReviewFactory.create_batch(3, submission=submission)
        response = self.get_page(submission, "list")
        self.assertContains(response, submission.title)
        self.assertContains(
            response, reverse("funds:submissions:detail", kwargs={"pk": submission.id})
        )
        for review in reviews:
            self.assertContains(response, review.author.reviewer.full_name)

    def test_draft_reviews_dont_appear(self):
        submission = ApplicationSubmissionFactory()
        review = ReviewFactory.create(submission=submission, is_draft=True)
        response = self.get_page(submission, "list")
        self.assertContains(response, submission.title)
        self.assertContains(
            response, reverse("funds:submissions:detail", kwargs={"pk": submission.id})
        )
        self.assertNotContains(response, review.author.reviewer.full_name)


class StaffReviewFormTestCase(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = "funds:submissions:reviews:{}"
    base_view_name = "review"
    submission = None

    def setUp(self):
        self.submission = ApplicationSubmissionFactory(status="internal_review")
        super().setUp()

    def get_kwargs(self, instance):
        return {"submission_pk": instance.id}

    def test_can_access_form(self):
        response = self.get_page(self.submission, "form")
        self.assertContains(response, self.submission.title)
        self.assertContains(
            response,
            reverse("funds:submissions:detail", kwargs={"pk": self.submission.id}),
        )

    def test_cant_access_wrong_status(self):
        submission = ApplicationSubmissionFactory(rejected=True)
        response = self.get_page(submission, "form")
        self.assertEqual(response.status_code, 403)

    def test_cant_resubmit_review(self):
        ReviewFactory(
            submission=self.submission, author__reviewer=self.user, author__staff=True
        )
        response = self.post_page(self.submission, {"data": "value"}, "form")
        self.assertEqual(response.context["has_submitted_review"], True)
        self.assertEqual(response.context["title"], "Update Review draft")

    def test_can_edit_draft_review(self):
        ReviewFactory(
            submission=self.submission,
            author__reviewer=self.user,
            author__staff=True,
            is_draft=True,
        )
        response = self.get_page(self.submission, "form")
        self.assertEqual(response.context["has_submitted_review"], False)
        self.assertEqual(response.context["title"], "Update Review draft")

    def test_revision_captured_on_review(self):
        form = self.submission.round.review_forms.first()

        data = ReviewFormFieldsFactory.form_response(form.fields)

        self.post_page(self.submission, data, "form")
        review = self.submission.reviews.first()
        self.assertEqual(review.revision, self.submission.live_revision)

    def test_can_submit_draft_review(self):
        form = self.submission.round.review_forms.first()

        data = ReviewFormFieldsFactory.form_response(form.fields)
        data["save_draft"] = True
        self.post_page(self.submission, data, "form")
        review = self.submission.reviews.first()
        self.assertTrue(review.is_draft)
        self.assertIsNone(review.revision)


class TestReviewScore(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = "funds:submissions:reviews:{}"
    base_view_name = "review"
    submission = None

    def setUp(self):
        super().setUp()
        self.submission = ApplicationSubmissionFactory(status="internal_review")

    def get_kwargs(self, instance):
        return {"submission_pk": instance.id}

    def submit_review_scores(self, scores=(), scores_without_text=()):
        if scores:
            form = ReviewFormFactory(
                form_fields__multiple__score=len(scores),
                form_fields__multiple__score_without_text=len(scores_without_text),
            )
        else:
            form = ReviewFormFactory(
                form_fields__exclude__score=True,
                form_fields__exclude__score_without_text=True,
            )
        review_form = self.submission.round.review_forms.first()
        review_form.form = form
        review_form.save()
        score_fields = {
            field.id: {"score": score}
            for field, score in zip(form.score_fields, scores, strict=False)
        }
        score_fields_without_text = {
            field.id: score
            for field, score in zip(
                form.score_fields_without_text, scores_without_text, strict=False
            )
        }
        score_fields.update(score_fields_without_text)
        data = ReviewFormFieldsFactory.form_response(form.form_fields, score_fields)

        # Make a new person for every review
        self.client.force_login(self.user_factory())
        response = self.post_page(self.submission, data, "form")
        # import ipdb; ipdb.set_trace()
        self.assertIn(
            "funds/applicationsubmission_admin_detail.html",
            response.template_name,
            msg="Failed to post the form correctly",
        )
        self.client.force_login(self.user)
        return self.submission.reviews.first()

    def test_score_calculated(self):
        review = self.submit_review_scores((5,), (5,))
        self.assertEqual(review.score, 5)

    def test_average_score_calculated(self):
        review = self.submit_review_scores((1, 5), (1, 5))
        self.assertEqual(review.score, (1 + 5) / 2)

    def test_no_score_is_NA(self):
        review = self.submit_review_scores()
        self.assertEqual(review.score, NA)

    def test_na_included_in_review_average(self):
        review = self.submit_review_scores((NA, 5))
        self.assertEqual(review.score, 2.5)

    def test_na_included_reviews_average(self):
        self.submit_review_scores((NA,))
        self.assertIsNotNone(Review.objects.score())

    def test_na_included_multiple_reviews_average(self):
        self.submit_review_scores((NA,))
        self.submit_review_scores((5,))

        self.assertEqual(Review.objects.count(), 2)
        self.assertEqual(Review.objects.score(), 2.5)


class UserReviewFormTestCase(BaseViewTestCase):
    user_factory = UserFactory
    url_name = "funds:submissions:reviews:{}"
    base_view_name = "review"

    def get_kwargs(self, instance):
        return {"submission_pk": instance.id}

    def test_cant_access_form(self):
        submission = ApplicationSubmissionFactory(status="internal_review")
        response = self.get_page(submission, "form")
        self.assertEqual(response.status_code, 403)


class ReviewDetailTestCase(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = "funds:submissions:reviews:{}"
    base_view_name = "review"

    def get_kwargs(self, instance):
        return {"pk": instance.id, "submission_pk": instance.submission.id}

    def test_review_detail_recommendation(self):
        submission = ApplicationSubmissionFactory(
            status="draft_proposal", workflow_stages=2
        )
        review = ReviewFactory(
            submission=submission, author__reviewer=self.user, recommendation_yes=True
        )
        response = self.get_page(review)
        self.assertContains(response, submission.title)
        self.assertContains(response, "Yes")

    def test_review_detail_opinion(self):
        staff = StaffFactory()
        submission = ApplicationSubmissionFactory(
            status="draft_proposal", workflow_stages=2
        )
        review = ReviewFactory(
            submission=submission, author__reviewer=self.user, recommendation_yes=True
        )
        ReviewOpinionFactory(
            review=review, author__reviewer=staff, opinion_disagree=True
        )
        response = self.get_page(review)
        self.assertContains(response, "Disagrees")


class ReviewListTestCase(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = "funds:submissions:reviews:{}"
    base_view_name = "list"

    def get_kwargs(self, instance):
        return {"submission_pk": instance.submission.id}

    def test_review_list_opinion(self):
        staff = StaffFactory()
        submission = ApplicationSubmissionFactory(
            status="draft_proposal", workflow_stages=2
        )
        review = ReviewFactory(
            submission=submission, author__reviewer=self.user, recommendation_yes=True
        )
        ReviewOpinionFactory(
            review=review, author__reviewer=staff, opinion_disagree=True
        )
        response = self.get_page(review)
        response_opinion = response.context["review_data"]["opinions"]["answers"][0]
        self.assertIn("Disagrees", response_opinion)
        self.assertIn(str(staff), response_opinion)


class StaffReviewOpinionCase(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = "funds:submissions:reviews:{}"
    base_view_name = "review"

    def setUp(self):
        super().setUp()
        self.submission = ApplicationSubmissionFactory(
            status="draft_proposal", workflow_stages=2
        )

    def get_kwargs(self, instance):
        return {"pk": instance.id, "submission_pk": instance.submission.id}

    def test_can_see_opinion_buttons_on_others_review(self):
        staff = StaffFactory()
        review = ReviewFactory(
            submission=self.submission,
            author__reviewer=staff,
            author__staff=True,
            recommendation_yes=True,
        )
        response = self.get_page(review)
        self.assertContains(response, 'name="agree"')

    def test_cant_see_opinion_buttons_on_self_review(self):
        review = ReviewFactory(
            submission=self.submission,
            author__reviewer=self.user,
            recommendation_yes=True,
        )
        response = self.get_page(review)
        self.assertNotContains(response, 'name="agree"')

    def test_can_add_opinion_to_others_review(self):
        staff = StaffFactory()
        review = ReviewFactory(
            submission=self.submission,
            author__reviewer=staff,
            author__staff=True,
            recommendation_yes=True,
        )
        response = self.post_page(review, {"agree": AGREE})
        self.assertTrue(
            review.opinions.first().opinion_display in Activity.objects.first().message
        )
        self.assertEqual(ReviewOpinion.objects.all().count(), 1)
        self.assertEqual(ReviewOpinion.objects.first().opinion, AGREE)
        url = self.url_from_pattern(
            "apply:submissions:reviews:review",
            kwargs={"submission_pk": self.submission.pk, "pk": review.id},
        )
        self.assertRedirects(response, url)

    def test_disagree_opinion_redirects_to_review_form(self):
        staff = StaffFactory()
        review = ReviewFactory(
            submission=self.submission,
            author__reviewer=staff,
            author__staff=True,
            recommendation_yes=True,
        )
        response = self.post_page(review, {"disagree": DISAGREE})
        url = self.url_from_pattern(
            "funds:submissions:reviews:form",
            kwargs={"submission_pk": self.submission.id},
        )
        self.assertRedirects(response, url)


class NonStaffReviewOpinionCase(BaseViewTestCase):
    user_factory = UserFactory
    url_name = "funds:submissions:reviews:{}"
    base_view_name = "review"
    submission = None

    def setUp(self):
        super().setUp()
        self.submission = ApplicationSubmissionFactory(
            status="draft_proposal", workflow_stages=2
        )

    def get_kwargs(self, instance):
        return {"pk": instance.id, "submission_pk": instance.submission.id}

    def test_nonstaff_cant_post_opinion_to_review(self):
        staff = StaffFactory()
        review = ReviewFactory(
            submission=self.submission,
            author__reviewer=staff,
            author__staff=True,
            recommendation_yes=True,
        )
        response = self.post_page(review, {"agree": AGREE})
        self.assertEqual(response.status_code, 403)


class ReviewDetailVisibilityTestCase(BaseViewTestCase):
    user_factory = ReviewerFactory
    url_name = "funds:submissions:reviews:{}"
    base_view_name = "review"

    def get_kwargs(self, instance):
        return {"pk": instance.id, "submission_pk": instance.submission.id}

    def test_review_detail_visibility_private(self):
        submission = ApplicationSubmissionFactory(
            status="external_review", workflow_stages=2
        )
        review = ReviewFactory(
            submission=submission, author__reviewer=self.user, visibility_private=True
        )
        self.client.force_login(self.user_factory())
        response = self.get_page(review)
        self.assertEqual(response.status_code, 403)

    def test_review_detail_visibility_reviewer(self):
        submission = ApplicationSubmissionFactory(
            status="external_review", workflow_stages=2
        )
        review = ReviewFactory(
            submission=submission, author__reviewer=self.user, visibility_reviewer=True
        )
        self.client.force_login(self.user_factory())
        response = self.get_page(review)
        self.assertEqual(response.status_code, 200)


class ReviewWorkFlowActionTestCase(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = "funds:submissions:reviews:{}"
    base_view_name = "review"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def get_kwargs(self, instance):
        return {"submission_pk": instance.id}

    def test_initial_state_transition_to_internal_review(self):
        submission = ApplicationSubmissionFactory(status=INITIAL_STATE)
        submission_stepped_phases = submission.workflow.stepped_phases
        form = submission.round.review_forms.first()

        data = ReviewFormFieldsFactory.form_response(form.fields)

        self.post_page(submission, data, "form")

        submission = ApplicationSubmission.objects.get(id=submission.id)
        self.assertEqual(submission.status, submission_stepped_phases[2][0].name)

    def test_proposal_discussion_to_proposal_internal_review(self):
        submission = ApplicationSubmissionFactory(
            status="proposal_discussion", workflow_stages=2
        )
        self.client.force_login(self.user_factory())
        fields = get_fields_for_stage(submission)
        data = ReviewFormFieldsFactory.form_response(fields)

        self.post_page(submission, data, "form")
        submission = ApplicationSubmission.objects.get(id=submission.id)
        self.assertEqual(submission.status, "proposal_internal_review")

    def test_internal_review_to_ready_for_discussion(self):
        submission = ApplicationSubmissionFactory(status="internal_review")
        submission_stepped_phases = submission.workflow.stepped_phases
        ReviewFactory(
            submission=submission, author__reviewer=self.user, visibility_private=True
        )

        self.client.force_login(self.user_factory())
        fields = get_fields_for_stage(submission)
        data = ReviewFormFieldsFactory.form_response(fields)

        self.post_page(submission, data, "form")
        submission = ApplicationSubmission.objects.get(id=submission.id)
        self.assertEqual(submission.status, submission_stepped_phases[3][0].name)

    def test_ext_external_review_to_ready_for_discussion(self):
        submission = ApplicationSubmissionFactory(
            status="ext_external_review", with_external_review=True
        )
        reviewers = ReviewerFactory.create_batch(2)
        AssignedReviewersFactory(submission=submission, reviewer=reviewers[0])
        AssignedReviewersFactory(submission=submission, reviewer=reviewers[1])
        ReviewFactory(
            submission=submission,
            author__reviewer=reviewers[0],
            visibility_private=True,
        )

        self.client.force_login(reviewers[1])
        fields = get_fields_for_stage(submission)
        data = ReviewFormFieldsFactory.form_response(fields)

        self.post_page(submission, data, "form")
        submission = ApplicationSubmission.objects.get(id=submission.id)
        self.assertEqual(submission.status, "ext_post_external_review_discussion")

    def test_com_external_review_to_ready_for_discussion(self):
        submission = ApplicationSubmissionFactory(
            status="com_external_review", workflow_name="single_com"
        )
        reviewers = ReviewerFactory.create_batch(2)
        AssignedReviewersFactory(submission=submission, reviewer=reviewers[0])
        AssignedReviewersFactory(submission=submission, reviewer=reviewers[1])
        ReviewFactory(
            submission=submission,
            author__reviewer=reviewers[0],
            visibility_private=True,
        )
        form = submission.round.review_forms.first()
        self.client.force_login(reviewers[1])
        data = ReviewFormFieldsFactory.form_response(form.fields)
        self.post_page(submission, data, "form")
        submission = ApplicationSubmission.objects.get(id=submission.id)
        self.assertEqual(submission.status, "com_post_external_review_discussion")

    def test_external_review_to_ready_for_discussion(self):
        submission = ApplicationSubmissionFactory(
            status="external_review", workflow_stages=2
        )
        reviewers = ReviewerFactory.create_batch(2)
        AssignedReviewersFactory(submission=submission, reviewer=reviewers[0])
        AssignedReviewersFactory(submission=submission, reviewer=reviewers[1])
        ReviewFactory(
            submission=submission,
            author__reviewer=reviewers[0],
            visibility_private=True,
        )

        self.client.force_login(reviewers[1])
        fields = get_fields_for_stage(submission)
        data = ReviewFormFieldsFactory.form_response(fields)

        self.post_page(submission, data, "form")
        submission = ApplicationSubmission.objects.get(id=submission.id)
        self.assertEqual(submission.status, "post_external_review_discussion")

    def test_submission_did_not_transition(self):
        submission = ApplicationSubmissionFactory(
            status="proposal_internal_review", workflow_stages=2
        )
        self.client.force_login(self.user_factory())
        fields = get_fields_for_stage(submission)
        data = ReviewFormFieldsFactory.form_response(fields)

        self.post_page(submission, data, "form")
        submission = ApplicationSubmission.objects.get(id=submission.id)
        self.assertEqual(submission.status, "proposal_internal_review")
