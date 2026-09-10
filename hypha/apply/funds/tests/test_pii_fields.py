"""Tests for marking form fields as containing personal information."""

import json
import re
import uuid

from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template
from django.test import TestCase, override_settings

from hypha.apply.categories.tests.factories import CategoryFactory, OptionFactory
from hypha.apply.determinations.blocks import DeterminationCustomFormFieldsBlock
from hypha.apply.funds.blocks import ApplicationCustomFormFieldsBlock
from hypha.apply.funds.models import ApplicationForm, ApplicationSubmission
from hypha.apply.funds.models.co_applicants import (
    CoApplicant,
    CoApplicantInvite,
    CoApplicantInviteStatus,
    CoApplicantRole,
)
from hypha.apply.funds.models.reviewer_role import ReviewerSettings
from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory
from hypha.apply.funds.wagtail_hooks import hide_pii_field_checkbox
from hypha.apply.projects.blocks import ProjectFormCustomFormFieldsBlock
from hypha.apply.review.blocks import ReviewCustomFormFieldsBlock
from hypha.apply.users.tests.factories import (
    ApplicantFactory,
    CommunityReviewerFactory,
    ReviewerFactory,
    StaffFactory,
    SuperUserFactory,
)
from hypha.home.factories import ApplySiteFactory

from ..permissions import can_view_submission_pii

REDACTED = "Hidden — contains personal information."


def mark_field_as_pii(submission, block_type="char"):
    """Mark the first field of `block_type` as PII and return its id and answer."""
    for index, field in enumerate(submission.form_fields):
        if field.block_type == block_type:
            submission.form_fields[index].value["is_pii"] = True
            submission.save()
            submission.refresh_from_db()
            return field.id, submission.data(field.id)
    raise AssertionError(f"No {block_type} field on the submission")


def add_category_field(submission, *, label="", is_pii=True):
    """Append a category question, mirroring how the form builder stores one.

    The category name and option value are distinctive rather than Faker words,
    because the tests assert on their absence from a page full of Faker text.
    """
    category = CategoryFactory(name="Category-name-xyzzy")
    option = OptionFactory(category=category, value="Option-value-xyzzy")
    field_id = str(uuid.uuid4())

    raw = list(submission.form_fields.raw_data)
    raw.append(
        {
            "id": field_id,
            "type": "category",
            "value": {
                "field_label": label,
                "help_text": "",
                "required": False,
                "is_pii": is_pii,
                "category": str(category.id),
                "multi": False,
            },
        }
    )
    submission.form_fields = json.dumps(raw)
    submission.form_data[field_id] = [str(option.id)]
    submission.save()
    submission.refresh_from_db()
    return field_id, category, option


def add_co_applicant(submission, user, role=CoApplicantRole.VIEW):
    invite = CoApplicantInvite.objects.create(
        submission=submission,
        invited_user_email=user.email,
        status=CoApplicantInviteStatus.ACCEPTED,
        role=role,
    )
    return CoApplicant.objects.create(
        submission=submission, user=user, invite=invite, role=role
    )


class TestCanViewSubmissionPII(TestCase):
    def test_staff_can_view(self):
        submission = ApplicationSubmissionFactory()
        self.assertTrue(can_view_submission_pii(StaffFactory(), submission))

    def test_superuser_can_view(self):
        submission = ApplicationSubmissionFactory()
        self.assertTrue(can_view_submission_pii(SuperUserFactory(), submission))

    def test_applicant_can_view_own_submission(self):
        applicant = ApplicantFactory()
        submission = ApplicationSubmissionFactory(user=applicant)
        self.assertTrue(can_view_submission_pii(applicant, submission))

    def test_co_applicant_can_view(self):
        co_user = ApplicantFactory()
        submission = ApplicationSubmissionFactory()
        add_co_applicant(submission, co_user)
        self.assertTrue(can_view_submission_pii(co_user, submission))

    def test_co_applicant_of_another_submission_cannot_view(self):
        co_user = ApplicantFactory()
        add_co_applicant(ApplicationSubmissionFactory(), co_user)
        self.assertFalse(
            can_view_submission_pii(co_user, ApplicationSubmissionFactory())
        )

    def test_reviewer_cannot_view(self):
        reviewer = ReviewerFactory()
        submission = ApplicationSubmissionFactory(reviewers=[reviewer])
        self.assertFalse(can_view_submission_pii(reviewer, submission))

    def test_community_reviewer_cannot_view(self):
        submission = ApplicationSubmissionFactory()
        self.assertFalse(
            can_view_submission_pii(CommunityReviewerFactory(), submission)
        )

    def test_unrelated_applicant_cannot_view(self):
        submission = ApplicationSubmissionFactory()
        self.assertFalse(can_view_submission_pii(ApplicantFactory(), submission))


class TestRedactedAnswers(TestCase):
    def test_answer_is_redacted(self):
        submission = ApplicationSubmissionFactory()
        __, answer = mark_field_as_pii(submission)

        redacted = submission.output_answers(redact_pii=True)
        self.assertNotIn(answer, redacted)
        self.assertIn(REDACTED, redacted)

    def test_question_is_still_shown(self):
        submission = ApplicationSubmissionFactory()
        field_id, __ = mark_field_as_pii(submission)
        label = submission.field(field_id).value["field_label"]

        self.assertIn(label, submission.output_answers(redact_pii=True))

    def test_answer_is_shown_when_not_redacting(self):
        submission = ApplicationSubmissionFactory()
        __, answer = mark_field_as_pii(submission)

        answers = submission.output_answers(redact_pii=False)
        self.assertIn(answer, answers)
        self.assertNotIn(REDACTED, answers)

    def test_unmarked_fields_are_untouched(self):
        submission = ApplicationSubmissionFactory()
        mark_field_as_pii(submission)
        unmarked = [
            field_id
            for field_id in submission.normal_blocks
            if not submission.field_is_pii(submission.field(field_id))
        ]
        self.assertTrue(unmarked)

        redacted = submission.output_answers(redact_pii=True)
        for field_id in unmarked:
            self.assertIn(submission.field(field_id).value["field_label"], redacted)

    def test_nothing_is_redacted_without_marked_fields(self):
        submission = ApplicationSubmissionFactory()
        self.assertNotIn(REDACTED, submission.output_answers(redact_pii=True))

    def test_render_answer_redacts_a_single_field(self):
        submission = ApplicationSubmissionFactory()
        field_id, answer = mark_field_as_pii(submission)

        self.assertIn(answer, submission.render_answer(field_id))
        self.assertNotIn(answer, submission.render_answer(field_id, redact_pii=True))

    def test_built_in_fields_cannot_be_marked(self):
        submission = ApplicationSubmissionFactory()
        for field in submission.form_fields:
            if field.block_type in ["title", "email", "full_name", "value", "duration"]:
                self.assertNotIn("is_pii", field.value)


class TestRenderSubmissionAnswersTag(TestCase):
    template = Template(
        "{% load workflow_tags %}"
        "{% render_submission_answers submission user preview=preview %}"
    )

    def render(self, submission, user, preview=False):
        return self.template.render(
            Context({"submission": submission, "user": user, "preview": preview})
        )

    def test_staff_sees_the_answer(self):
        submission = ApplicationSubmissionFactory()
        __, answer = mark_field_as_pii(submission)

        self.assertIn(answer, self.render(submission, StaffFactory()))

    def test_applicant_sees_their_own_answer(self):
        applicant = ApplicantFactory()
        submission = ApplicationSubmissionFactory(user=applicant)
        __, answer = mark_field_as_pii(submission)

        self.assertIn(answer, self.render(submission, applicant))

    def test_co_applicant_sees_the_answer(self):
        co_user = ApplicantFactory()
        submission = ApplicationSubmissionFactory()
        add_co_applicant(submission, co_user)
        __, answer = mark_field_as_pii(submission)

        self.assertIn(answer, self.render(submission, co_user))

    def test_reviewer_does_not_see_the_answer(self):
        reviewer = ReviewerFactory()
        submission = ApplicationSubmissionFactory(reviewers=[reviewer])
        __, answer = mark_field_as_pii(submission)

        rendered = self.render(submission, reviewer)
        self.assertNotIn(answer, rendered)
        self.assertIn(REDACTED, rendered)


class TestSubmissionDetailRedaction(TestCase):
    def setUp(self):
        apply_site = ApplySiteFactory()
        ReviewerSettings.objects.get_or_create(site_id=apply_site.id)

    def get_detail(self, submission, user):
        self.client.force_login(user)
        return self.client.get(
            f"/apply/submissions/{submission.id}/", follow=True, secure=True
        )

    def test_reviewer_does_not_see_the_answer(self):
        reviewer = ReviewerFactory()
        submission = ApplicationSubmissionFactory(reviewers=[reviewer])
        __, answer = mark_field_as_pii(submission)

        response = self.get_detail(submission, reviewer)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, answer)
        self.assertContains(response, REDACTED)

    def test_staff_sees_the_answer(self):
        submission = ApplicationSubmissionFactory()
        __, answer = mark_field_as_pii(submission)

        response = self.get_detail(submission, StaffFactory())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, answer)


class TestPIICheckboxVisibility(TestCase):
    @override_settings(PII_FIELD_MARKING_ENABLED=False)
    def test_checkbox_is_hidden_by_default(self):
        self.assertIn('[data-contentpath="is_pii"]', hide_pii_field_checkbox())

    @override_settings(PII_FIELD_MARKING_ENABLED=True)
    def test_checkbox_is_shown_when_enabled(self):
        self.assertEqual(hide_pii_field_checkbox(), "")


class TestLegacyFormFields(TestCase):
    def test_read_path_and_backfill_for_data_without_is_pii(self):
        submission = ApplicationSubmissionFactory()

        # Simulate pre-migration data: strip is_pii from the stored JSON.
        raw = list(submission.form_fields.raw_data)
        for block in raw:
            if isinstance(block.get("value"), dict):
                block["value"].pop("is_pii", None)
        type(submission).objects.filter(pk=submission.pk).update(
            form_fields=json.dumps(raw)
        )
        submission.refresh_from_db()

        stored = list(submission.form_fields.raw_data)
        assert all(
            "is_pii" not in b["value"]
            for b in stored
            if isinstance(b.get("value"), dict)
        ), "setup failed"

        # Read path must cope with the key being absent.
        for field_id in submission.normal_blocks:
            self.assertFalse(submission.field_is_pii(submission.field(field_id)))
        self.assertNotIn(
            REDACTED,
            submission.output_answers(redact_pii=True),
        )

        # There is no data migration: re-saving through the current block
        # definition is what writes the explicit default, whenever that next
        # happens to occur.
        list(submission.form_fields)
        submission.save(update_fields=["form_fields"])
        submission.refresh_from_db()

        after = list(submission.form_fields.raw_data)
        pii_capable = [b for b in after if b["type"] in ("char", "text", "rich_text")]
        self.assertTrue(pii_capable)
        for block in pii_capable:
            self.assertIs(block["value"]["is_pii"], False)

        # Built-in fields must not gain the key.
        for block in after:
            if block["type"] in ("title", "email", "full_name", "value", "duration"):
                self.assertNotIn("is_pii", block["value"])


class TestFormBuilderAdmin(TestCase):
    def get_edit_page(self):
        form = ApplicationForm.objects.create(name="Test form", form_fields="[]")
        self.client.force_login(SuperUserFactory())
        return self.client.get(
            f"/admin/funds/applicationform/edit/{form.pk}/", secure=True, follow=True
        )

    @override_settings(PII_FIELD_MARKING_ENABLED=True)
    def test_checkbox_present_and_visible_when_enabled(self):
        response = self.get_edit_page()
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("is_pii", content)
        self.assertIn("Personal information", content)
        self.assertNotIn('[data-contentpath="is_pii"]{display:none}', content)

    @override_settings(PII_FIELD_MARKING_ENABLED=False)
    def test_checkbox_hidden_when_disabled(self):
        response = self.get_edit_page()
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("is_pii", content)
        self.assertIn('[data-contentpath="is_pii"]{display:none}', content)


class TestCategoryQuestionLabel(TestCase):
    """A category question may leave its label blank to use the category's own."""

    def test_blank_label_falls_back_to_category_name_when_visible(self):
        submission = ApplicationSubmissionFactory()
        __, category, __ = add_category_field(submission, is_pii=False)

        self.assertIn(category.name, submission.output_answers(redact_pii=False))

    def test_blank_label_falls_back_to_category_name_when_redacted(self):
        submission = ApplicationSubmissionFactory()
        __, category, option = add_category_field(submission, is_pii=True)

        rendered = submission.output_answers(redact_pii=True)
        self.assertNotIn(option.value, rendered)
        self.assertIn(category.name, rendered)
        self.assertIn(REDACTED, rendered)

    def test_explicit_label_is_kept_when_redacted(self):
        submission = ApplicationSubmissionFactory()
        __, category, option = add_category_field(
            submission, label="Your date of birth", is_pii=True
        )

        rendered = submission.output_answers(redact_pii=True)
        self.assertIn("Your date of birth", rendered)
        self.assertNotIn(category.name, rendered)
        self.assertNotIn(option.value, rendered)


class TestPIIMarker(TestCase):
    """Staff get a "(PII)" marker so they can see which answers are restricted."""

    template = Template(
        "{% load workflow_tags %}{% render_submission_answers submission user %}"
    )

    def render(self, submission, user):
        return self.template.render(Context({"submission": submission, "user": user}))

    def test_staff_see_the_marker(self):
        submission = ApplicationSubmissionFactory()
        field_id, answer = mark_field_as_pii(submission)
        label = submission.field(field_id).value["field_label"]

        rendered = self.render(submission, StaffFactory())
        self.assertIn(answer, rendered)
        self.assertIn("(PII)", rendered)
        self.assertIn("Contains personal information.", rendered)
        # The marker sits after the label, inside the question heading.
        self.assertRegex(rendered, rf"{re.escape(label)}\s*<span[^>]*>\(PII\)</span>")

    def test_marker_is_not_shown_on_unmarked_fields(self):
        submission = ApplicationSubmissionFactory()
        self.assertNotIn("(PII)", self.render(submission, StaffFactory()))

    def test_applicant_does_not_see_the_marker(self):
        applicant = ApplicantFactory()
        submission = ApplicationSubmissionFactory(user=applicant)
        __, answer = mark_field_as_pii(submission)

        rendered = self.render(submission, applicant)
        self.assertIn(answer, rendered)
        self.assertNotIn("(PII)", rendered)

    def test_co_applicant_does_not_see_the_marker(self):
        co_user = ApplicantFactory()
        submission = ApplicationSubmissionFactory()
        add_co_applicant(submission, co_user)
        mark_field_as_pii(submission)

        self.assertNotIn("(PII)", self.render(submission, co_user))

    def test_reviewer_does_not_see_the_marker(self):
        reviewer = ReviewerFactory()
        submission = ApplicationSubmissionFactory(reviewers=[reviewer])
        mark_field_as_pii(submission)

        rendered = self.render(submission, reviewer)
        self.assertNotIn("(PII)", rendered)
        self.assertIn(REDACTED, rendered)


class TestApplicantPreview(TestCase):
    """An application can be filled in anonymously when
    FORCE_LOGIN_FOR_APPLICATION is off, so the previewing applicant cannot be
    recognised as the author of what they just wrote.
    """

    template = Template(
        "{% load workflow_tags %}"
        "{% render_submission_answers submission user preview=preview %}"
    )

    def render(self, submission, user, preview):
        return self.template.render(
            Context({"submission": submission, "user": user, "preview": preview})
        )

    def test_anonymous_applicant_sees_own_answers_in_preview(self):
        submission = ApplicationSubmissionFactory()
        __, answer = mark_field_as_pii(submission)
        # process_form_submission stores no user for an anonymous application.
        ApplicationSubmission.objects.filter(pk=submission.pk).update(user=None)
        submission.refresh_from_db()

        rendered = self.render(submission, AnonymousUser(), preview=True)
        self.assertIn(answer, rendered)
        self.assertNotIn(REDACTED, rendered)
        self.assertNotIn("(PII)", rendered)

    def test_anonymous_user_is_still_redacted_outside_a_preview(self):
        submission = ApplicationSubmissionFactory()
        __, answer = mark_field_as_pii(submission)
        ApplicationSubmission.objects.filter(pk=submission.pk).update(user=None)
        submission.refresh_from_db()

        rendered = self.render(submission, AnonymousUser(), preview=False)
        self.assertNotIn(answer, rendered)
        self.assertIn(REDACTED, rendered)

    def test_reviewer_preview_flag_does_not_leak_via_the_detail_page(self):
        # The detail page never sets `preview`, so the flag cannot be reached
        # by anyone browsing an existing submission.
        reviewer = ReviewerFactory()
        submission = ApplicationSubmissionFactory(reviewers=[reviewer])
        __, answer = mark_field_as_pii(submission)

        rendered = self.render(submission, reviewer, preview=False)
        self.assertNotIn(answer, rendered)


class TestPIICheckboxIsApplicationFormsOnly(TestCase):
    """Only application form answers are redacted, so only they get the
    checkbox. See `NoPIIMarkingMixin`.
    """

    def field_blocks_with_checkbox(self, block_class):
        return sorted(
            name
            for name, block in block_class().child_blocks.items()
            if "is_pii" in getattr(block, "child_blocks", {})
        )

    def test_application_form_fields_have_the_checkbox(self):
        self.assertIn(
            "char", self.field_blocks_with_checkbox(ApplicationCustomFormFieldsBlock)
        )

    def test_other_forms_do_not_have_the_checkbox(self):
        for block_class in (
            ReviewCustomFormFieldsBlock,
            DeterminationCustomFormFieldsBlock,
            ProjectFormCustomFormFieldsBlock,
        ):
            with self.subTest(block=block_class.__name__):
                self.assertEqual(self.field_blocks_with_checkbox(block_class), [])

    def test_removing_it_elsewhere_leaves_application_forms_alone(self):
        # The field blocks are declared as class attributes, so a careless
        # removal would strip the checkbox from every form at once.
        ReviewCustomFormFieldsBlock()
        ProjectFormCustomFormFieldsBlock()

        self.assertIn(
            "char", self.field_blocks_with_checkbox(ApplicationCustomFormFieldsBlock)
        )


class TestCategoryQuestionLabelIsNotPersisted(TestCase):
    def test_rendering_does_not_write_the_fallback_label_back(self):
        submission = ApplicationSubmissionFactory()
        field_id, category, __ = add_category_field(submission, label="")

        submission.output_answers(redact_pii=True)
        submission.output_answers(redact_pii=False)

        block = next(
            block
            for block in submission.form_fields.raw_data
            if block["id"] == field_id
        )
        self.assertEqual(block["value"]["field_label"], "")

        field = submission.field(field_id)
        self.assertEqual(field.value["field_label"], "")
        self.assertEqual(
            field.block.get_display_value(field.value)["field_label"], category.name
        )
