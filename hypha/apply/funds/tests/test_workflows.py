"""Tests for the workflow registry, focused on the external-then-internal workflow."""

from types import SimpleNamespace
from unittest import mock

import pytest
from django.test import SimpleTestCase
from django.utils.translation import gettext_lazy, override

from hypha.apply.users.tests.factories import StaffFactory

from ..models.submissions import get_all_possible_states
from ..workflows import (
    DETERMINATION_OUTCOMES,
    INITIAL_STATE,
    WORKFLOWS,
    accepted_statuses,
    dismissed_statuses,
    ext_or_higher_statuses,
    ext_review_statuses,
    review_statuses,
)
from ..workflows.constants import DETERMINATION_RESPONSE_PHASES
from ..workflows.models.phase import Phase
from ..workflows.permissions import staff_edit_permissions
from .factories import ApplicationSubmissionFactory

WORKFLOW_NAME = "single_ext_int"


class TestRequestExternalInternalWorkflow(SimpleTestCase):
    @property
    def workflow(self):
        return WORKFLOWS[WORKFLOW_NAME]

    def test_workflow_is_registered(self):
        self.assertIn(WORKFLOW_NAME, WORKFLOWS)
        self.assertEqual(
            str(self.workflow.name), "Request external then internal review"
        )

    def test_phases_and_steps(self):
        expected = {
            "draft": 0,
            "in_discussion": 1,
            "ext_int_more_info": 1,
            "ext_int_screened": 2,
            "ext_int_external_review": 3,
            "ext_int_post_external_review_discussion": 4,
            "ext_int_post_external_review_more_info": 4,
            "ext_int_internal_review": 5,
            "ext_int_post_review_discussion": 6,
            "ext_int_post_review_more_info": 6,
            "ext_int_determination": 7,
            "ext_int_accepted": 8,
            "ext_int_waitlisted": 8,
            "ext_int_rejected": 8,
        }
        self.assertEqual(
            {name: phase.step for name, phase in self.workflow.items()}, expected
        )

    def test_ready_for_review_comes_before_external_review(self):
        self.assertLess(
            self.workflow["ext_int_screened"].step,
            self.workflow["ext_int_external_review"].step,
        )
        # Screening can only reach the external review through the new phase.
        self.assertNotIn(
            "ext_int_external_review", self.workflow[INITIAL_STATE].transitions
        )
        self.assertIn("ext_int_screened", self.workflow[INITIAL_STATE].transitions)

    def test_ready_for_review_is_hidden_from_the_applicant(self):
        applicant = SimpleNamespace(
            is_apply_staff=False, is_applicant=True, is_reviewer=False
        )
        reviewer = SimpleNamespace(
            is_apply_staff=False, is_applicant=False, is_reviewer=True
        )
        phase = self.workflow["ext_int_screened"]
        self.assertEqual(phase.display_name, "Ready for Review")
        self.assertFalse(phase.permissions.can_view(applicant))
        self.assertTrue(phase.permissions.can_view(reviewer))
        # Reviewers only get to review once the external review is opened.
        self.assertFalse(phase.permissions.can_review(reviewer))

    def test_external_review_comes_before_internal_review(self):
        self.assertLess(
            self.workflow["ext_int_external_review"].step,
            self.workflow["ext_int_internal_review"].step,
        )

    def test_single_stage_with_external_review(self):
        (stage,) = self.workflow.stages
        self.assertEqual(stage.name, "RequestExtInt")
        self.assertTrue(stage.has_external_review)

    def test_waitlisted_is_not_a_determination_outcome(self):
        self.assertNotIn("ext_int_waitlisted", DETERMINATION_OUTCOMES)

    def test_waitlisted_transitions(self):
        self.assertEqual(
            set(self.workflow["ext_int_waitlisted"].transitions),
            {"ext_int_accepted", "ext_int_rejected", "ext_int_determination"},
        )

    def test_waitlist_offered_from_discussion_and_determination(self):
        for phase_name in [
            "ext_int_post_review_discussion",
            "ext_int_determination",
        ]:
            with self.subTest(phase=phase_name):
                self.assertIn(
                    "ext_int_waitlisted", self.workflow[phase_name].transitions
                )

    def test_dismissed_is_softened_for_the_applicant(self):
        rejected = self.workflow["ext_int_rejected"]
        self.assertEqual(rejected.display_name, "Dismissed")
        self.assertEqual(rejected.public_name, "Not Accepted")

    def test_outcome_phases_are_terminal(self):
        for phase_name in ["ext_int_accepted", "ext_int_rejected"]:
            with self.subTest(phase=phase_name):
                self.assertEqual(self.workflow[phase_name].transitions, {})

    def test_picked_up_by_derived_status_sets(self):
        self.assertIn("ext_int_external_review", ext_review_statuses)
        self.assertNotIn("ext_int_screened", ext_review_statuses)
        self.assertNotIn("ext_int_screened", ext_or_higher_statuses)
        self.assertIn("ext_int_internal_review", ext_or_higher_statuses)
        self.assertIn("ext_int_accepted", accepted_statuses)
        self.assertIn("ext_int_rejected", dismissed_statuses)

    def test_ready_for_review_is_not_a_review_status(self):
        # Reviewers are notified for everything in review_statuses, and they
        # can not review while the application is only screened.
        self.assertNotIn("ext_int_screened", review_statuses)
        self.assertIn("ext_int_external_review", review_statuses)
        self.assertIn("ext_int_internal_review", review_statuses)

    def test_both_discussions_expect_a_determination(self):
        # An application can be decided straight after the external review,
        # without opening the internal one.
        self.assertIn(
            "ext_int_post_external_review_discussion", DETERMINATION_RESPONSE_PHASES
        )
        self.assertIn("ext_int_post_review_discussion", DETERMINATION_RESPONSE_PHASES)


@pytest.mark.django_db
def test_walk_the_whole_workflow():
    """The generated FSM transitions actually fire, in the intended order."""
    staff = StaffFactory()
    submission = ApplicationSubmissionFactory(workflow_name=WORKFLOW_NAME)
    assert submission.status == "in_discussion"

    chain = [
        "ext_int_screened",
        "ext_int_external_review",
        "ext_int_post_external_review_discussion",
        "ext_int_internal_review",
        "ext_int_post_review_discussion",
        "ext_int_determination",
        "ext_int_waitlisted",
        "ext_int_accepted",
    ]
    for target in chain:
        submission.perform_transition(target, staff)
        submission.save()
        assert submission.status == target

    assert submission.phase.display_name == "Accepted"


class TestPhaseSourceNames(SimpleTestCase):
    """The names the code matches on must not follow the active language."""

    def phase(self, display):
        return Phase(
            "a_phase",
            display,
            stage=None,
            permissions=staff_edit_permissions,
            step=0,
        )

    def test_source_name_slug_and_colour_ignore_the_active_language(self):
        with override("cs"):
            accepted = self.phase(gettext_lazy("Accepted"))
            discussion = self.phase(gettext_lazy("Ready for Discussion"))

        # Sanity check that "cs" really does translate these.
        self.assertNotEqual(accepted.display_name, "Accepted")

        self.assertEqual(accepted.display_name_source, "Accepted")
        self.assertEqual(accepted.display_slug, "accepted")
        self.assertEqual(accepted.bg_color, "bg-green-200")
        self.assertEqual(discussion.display_name_source, "Ready for Discussion")
        self.assertEqual(discussion.display_slug, "ready-for-discussion")
        self.assertEqual(discussion.bg_color, "bg-blue-100")

    def test_status_choices_ignore_the_active_language(self):
        # These choices are written into migrations, so phases built on a
        # non-English install must not label them in that language.
        with override("cs"):
            phase = self.phase(gettext_lazy("Accepted"))

        with mock.patch.dict(WORKFLOWS, {"fake": {"a_phase": phase}}, clear=True):
            self.assertEqual(get_all_possible_states(), [("a_phase", "Accepted")])
