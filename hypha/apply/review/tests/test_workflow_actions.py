"""Tests for the automatic transitions triggered by submitting a review."""

import pytest
from django.test import RequestFactory

from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory
from hypha.apply.users.tests.factories import StaffFactory

from ..views import review_workflow_actions
from .factories import ReviewFactory

WORKFLOW_NAME = "single_ext_int"


def submission_in(status, staff):
    """Walk a new external-then-internal submission up to `status`."""
    submission = ApplicationSubmissionFactory(workflow_name=WORKFLOW_NAME)
    chain = [
        "ext_int_screened",
        "ext_int_external_review",
        "ext_int_post_external_review_discussion",
        "ext_int_internal_review",
    ]
    for target in chain:
        submission.perform_transition(target, staff)
        submission.save()
        if target == status:
            break
    return submission


def request_for(user):
    request = RequestFactory().get("/")
    request.user = user
    return request


@pytest.mark.django_db
def test_external_review_closes_after_enough_reviewer_reviews(settings):
    settings.TRANSITION_AFTER_REVIEWS = 2
    staff = StaffFactory()
    submission = submission_in("ext_int_external_review", staff)

    ReviewFactory.create_batch(2, submission=submission)

    review_workflow_actions(request_for(staff), submission)

    assert submission.status == "ext_int_post_external_review_discussion"


@pytest.mark.django_db
def test_internal_review_is_not_closed_by_the_earlier_reviews(settings):
    """The external reviews must not count towards closing the internal one."""
    settings.TRANSITION_AFTER_REVIEWS = 2
    staff = StaffFactory()
    submission = submission_in("ext_int_internal_review", staff)

    # Two reviews from the external round plus a first staff review.
    ReviewFactory.create_batch(2, submission=submission)
    ReviewFactory(submission=submission, author__staff=True)

    review_workflow_actions(request_for(staff), submission)

    assert submission.status == "ext_int_internal_review"
