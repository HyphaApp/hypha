import json

from django.db.models import Model as DjangoModel
from django.utils import timezone
from django.utils.translation import gettext as _

from hypha.apply.activity.models import ALL, APPLICANT, TEAM
from hypha.apply.activity.options import MESSAGES
from hypha.apply.projects.utils import (
    get_invoice_public_status,
    get_project_public_status,
    get_project_status_display_value,
)

from .base import AdapterBase
from .utils import is_invoice_public_transition, is_transition, reviewers_message


class ActivityAdapter(AdapterBase):
    adapter_type = "Activity Feed"
    always_send = True
    messages = {
        MESSAGES.TRANSITION: "handle_transition",
        MESSAGES.BATCH_TRANSITION: "handle_batch_transition",
        MESSAGES.NEW_SUBMISSION: _("Submitted {source.title} for {source.page.title}"),
        MESSAGES.EDIT_SUBMISSION: _("Edited"),
        MESSAGES.APPLICANT_EDIT: _("Edited"),
        MESSAGES.UPDATE_LEAD: _("Lead changed from {old_lead} to {source.lead}"),
        MESSAGES.BATCH_UPDATE_LEAD: _("Batch Lead changed to {new_lead}"),
        MESSAGES.DETERMINATION_OUTCOME: _(
            "Sent a determination. Outcome: {determination.clean_outcome}"
        ),
        MESSAGES.BATCH_DETERMINATION_OUTCOME: "batch_determination",
        MESSAGES.INVITED_TO_PROPOSAL: _("Invited to submit a proposal"),
        MESSAGES.REVIEWERS_UPDATED: "reviewers_updated",
        MESSAGES.BATCH_REVIEWERS_UPDATED: "batch_reviewers_updated",
        MESSAGES.PARTNERS_UPDATED: "partners_updated",
        MESSAGES.NEW_REVIEW: _("Submitted a review"),
        MESSAGES.OPENED_SEALED: _("Opened the submission while still sealed"),
        MESSAGES.SCREENING: "handle_screening_statuses",
        MESSAGES.REVIEW_OPINION: _(
            "{user} {opinion.opinion_display}s with {opinion.review.author}s review of {source}"
        ),
        MESSAGES.DELETE_REVIEW_OPINION: _(
            "{user} deleted the opinion for review: {review_opinion.review}"
        ),
        MESSAGES.CREATED_PROJECT: _("Created project"),
        MESSAGES.PROJECT_TRANSITION: "handle_project_transition",
        MESSAGES.UPDATE_PROJECT_LEAD: _(
            "Lead changed from {old_lead} to {source.lead}"
        ),
        MESSAGES.SEND_FOR_APPROVAL: _("Requested approval"),
        MESSAGES.APPROVE_PAF: "handle_paf_assignment",
        MESSAGES.APPROVE_PROJECT: _("Approved"),
        MESSAGES.REQUEST_PROJECT_CHANGE: _(
            'Requested changes for acceptance: "{comment}"'
        ),
        MESSAGES.SUBMIT_CONTRACT_DOCUMENTS: _("Submitted Contract Documents"),
        MESSAGES.UPLOAD_CONTRACT: _("Uploaded a {contract.state} contract"),
        MESSAGES.APPROVE_CONTRACT: _("Approved contract"),
        MESSAGES.UPDATE_INVOICE_STATUS: "handle_update_invoice_status",
        MESSAGES.CREATE_INVOICE: _("Invoice added"),
        MESSAGES.SUBMIT_REPORT: _("Submitted a report"),
        MESSAGES.SKIPPED_REPORT: "handle_skipped_report",
        MESSAGES.REPORT_FREQUENCY_CHANGED: "handle_report_frequency",
        MESSAGES.DISABLED_REPORTING: _("Reporting disabled"),
        MESSAGES.BATCH_DELETE_SUBMISSION: "handle_batch_delete_submission",
        MESSAGES.BATCH_ARCHIVE_SUBMISSION: "handle_batch_archive_submission",
        MESSAGES.ARCHIVE_SUBMISSION: _(
            "{user} has archived the submission: {source.title}"
        ),
        MESSAGES.UNARCHIVE_SUBMISSION: _(
            "{user} has unarchived the submission: {source.title}"
        ),
        MESSAGES.DELETE_INVOICE: _("Deleted an invoice"),
    }

    def recipients(self, message_type, **kwargs):
        return [None]

    def extra_kwargs(self, message_type, source, sources, **kwargs):
        if message_type in [
            MESSAGES.OPENED_SEALED,
            MESSAGES.REVIEWERS_UPDATED,
            MESSAGES.SCREENING,
            MESSAGES.REVIEW_OPINION,
            MESSAGES.DELETE_REVIEW_OPINION,
            MESSAGES.BATCH_REVIEWERS_UPDATED,
            MESSAGES.PARTNERS_UPDATED,
            MESSAGES.APPROVE_PROJECT,
            MESSAGES.REQUEST_PROJECT_CHANGE,
            MESSAGES.SEND_FOR_APPROVAL,
            MESSAGES.APPROVE_PAF,
            MESSAGES.NEW_REVIEW,
            MESSAGES.UPDATE_PROJECT_LEAD,
        ]:
            return {"visibility": TEAM}

        if message_type in [
            MESSAGES.CREATED_PROJECT,
            MESSAGES.APPROVE_CONTRACT,
            MESSAGES.UPLOAD_CONTRACT,
            MESSAGES.SUBMIT_CONTRACT_DOCUMENTS,
            MESSAGES.DELETE_INVOICE,
            MESSAGES.CREATE_INVOICE,
        ]:
            return {"visibility": APPLICANT}

        source = source or sources[0]
        if is_transition(message_type) and not source.phase.permissions.can_view(
            source.user
        ):
            # User's shouldn't see status activity changes for stages that aren't visible to the them
            return {"visibility": TEAM}

        if message_type == MESSAGES.UPDATE_INVOICE_STATUS:
            invoice = kwargs.get("invoice", None)
            if invoice and not is_invoice_public_transition(invoice):
                return {"visibility": TEAM}
            return {"visibility": APPLICANT}
        return {}

    def reviewers_updated(self, added=None, removed=None, **kwargs):
        message = [_("Reviewers updated.")]
        if added:
            message.append(_("Added:"))
            message.extend(reviewers_message(added))

        if removed:
            message.append(_("Removed:"))
            message.extend(reviewers_message(removed))

        return " ".join(message)

    def batch_reviewers_updated(self, added, **kwargs):
        base = [_("Batch Reviewers Updated.")]
        base.extend(
            [
                _("{user} as {name}.").format(user=str(user), name=role.name)
                for role, user in added
                if user
            ]
        )
        return " ".join(base)

    def batch_determination(self, sources, determinations, **kwargs):
        submission = sources[0]
        determination = determinations[submission.id]
        return self.messages[MESSAGES.DETERMINATION_OUTCOME].format(
            determination=determination,
        )

    def handle_batch_delete_submission(self, sources, **kwargs):
        submissions = sources
        submissions_text = ", ".join([submission.title for submission in submissions])
        return _("Successfully deleted submissions: {title}").format(
            title=submissions_text
        )

    def handle_batch_archive_submission(self, sources, **kwargs):
        submissions = sources
        submissions_text = ", ".join([submission.title for submission in submissions])
        return _("Successfully archived submissions: {title}").format(
            title=submissions_text
        )

    def handle_paf_assignment(self, source, paf_approvals, **kwargs):
        if hasattr(paf_approvals, "__iter__"):  # paf_approvals has to be iterable
            users = ", ".join(
                [
                    paf_approval.user.full_name
                    if paf_approval.user.full_name
                    else paf_approval.user.username
                    for paf_approval in paf_approvals
                ]
            )
            users_sentence = " and".join(users.rsplit(",", 1))
            return _("PAF assigned to {}").format(users_sentence)
        return None

    def handle_transition(self, old_phase, source, **kwargs):
        submission = source
        base_message = _("Progressed from {old_display} to {new_display}")

        new_phase = submission.phase

        staff_message = base_message.format(
            old_display=old_phase.display_name,
            new_display=new_phase.display_name,
        )

        if new_phase.permissions.can_view(submission.user):
            # we need to provide a different message to the applicant
            if not old_phase.permissions.can_view(submission.user):
                old_phase = submission.workflow.previous_visible(
                    old_phase, submission.user
                )

            applicant_message = base_message.format(
                old_display=old_phase.public_name,
                new_display=new_phase.public_name,
            )

            return json.dumps(
                {
                    TEAM: staff_message,
                    ALL: applicant_message,
                }
            )

        return staff_message

    def handle_project_transition(self, old_stage, source, **kwargs):
        project = source
        base_message = _("Progressed from {old_display} to {new_display}")

        staff_message = base_message.format(
            old_display=get_project_status_display_value(old_stage),
            new_display=project.status_display,
        )

        applicant_message = base_message.format(
            old_display=get_project_public_status(project_status=old_stage),
            new_display=get_project_public_status(project_status=project.status),
        )

        return json.dumps(
            {
                TEAM: staff_message,
                ALL: applicant_message,
            }
        )

    def handle_batch_transition(self, transitions, sources, **kwargs):
        submissions = sources
        kwargs.pop("source")
        for submission in submissions:
            old_phase = transitions[submission.id]
            return self.handle_transition(
                old_phase=old_phase, source=submission, **kwargs
            )

    def partners_updated(self, added, removed, **kwargs):
        message = [_("Partners updated.")]
        if added:
            message.append(_("Added:"))
            message.append(", ".join([str(user) for user in added]) + ".")

        if removed:
            message.append(_("Removed:"))
            message.append(", ".join([str(user) for user in removed]) + ".")

        return " ".join(message)

    def handle_report_frequency(self, config, **kwargs):
        new_schedule = config.get_frequency_display()
        return _(
            "Updated reporting frequency. New schedule is: {new_schedule} starting on {schedule_start}"
        ).format(new_schedule=new_schedule, schedule_start=config.schedule_start)

    def handle_skipped_report(self, report, **kwargs):
        if report.skipped:
            return "Skipped a Report"
        else:
            return "Marked a Report as required"

    def handle_update_invoice_status(self, invoice, **kwargs):
        base_message = _("Updated Invoice status to: {invoice_status}.")
        staff_message = base_message.format(invoice_status=invoice.get_status_display())

        if is_invoice_public_transition(invoice):
            public_status = get_invoice_public_status(invoice_status=invoice.status)
            applicant_message = base_message.format(invoice_status=public_status)
            return json.dumps({TEAM: staff_message, ALL: applicant_message})

        return staff_message

    def send_message(self, message, user, source, sources, **kwargs):
        from ..models import Activity

        visibility = kwargs.get("visibility", ALL)

        related = kwargs["related"]
        if isinstance(related, dict):
            try:
                related = related[source.id]
            except KeyError:
                pass

        has_correct_fields = all(
            hasattr(related, attr) for attr in ["get_absolute_url"]
        )
        isnt_source = source != related
        is_model = isinstance(related, DjangoModel)
        if has_correct_fields and isnt_source and is_model:
            related_object = related
        else:
            related_object = None

        Activity.actions.create(
            user=user,
            source=source,
            timestamp=timezone.now(),
            message=message,
            visibility=visibility,
            related_object=related_object,
        )

    def handle_screening_statuses(self, source, old_status, **kwargs):
        new_status = ", ".join([s.title for s in source.screening_statuses.all()])
        return _("Screening decision from {old_status} to {new_status}").format(
            old_status=old_status, new_status=new_status
        )
