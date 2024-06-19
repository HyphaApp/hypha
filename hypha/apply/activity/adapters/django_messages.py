from django.contrib import messages
from django.utils.translation import gettext as _

from hypha.apply.activity.options import MESSAGES

from .base import AdapterBase


class DjangoMessagesAdapter(AdapterBase):
    adapter_type = "Django"
    always_send = True

    messages = {
        MESSAGES.BATCH_REVIEWERS_UPDATED: "batch_reviewers_updated",
        MESSAGES.BATCH_TRANSITION: "batch_transition",
        MESSAGES.BATCH_DETERMINATION_OUTCOME: "batch_determinations",
        MESSAGES.REMOVE_DOCUMENT: _("Successfully removed document"),
        MESSAGES.SKIPPED_REPORT: "handle_skipped_report",
        MESSAGES.REPORT_FREQUENCY_CHANGED: "handle_report_frequency",
        MESSAGES.DISABLED_REPORTING: _("Reporting disabled"),
        MESSAGES.CREATE_REMINDER: _("Reminder created"),
        MESSAGES.DELETE_REMINDER: _("Reminder deleted"),
    }

    def batch_reviewers_updated(self, added, sources, **kwargs):
        reviewers_text = " ".join(
            [
                _("{user} as {name},").format(user=str(user), name=role.name)
                for role, user in added
                if user
            ]
        )

        return _("Batch reviewers added: {reviewers_text} to ").format(
            reviewers_text=reviewers_text
        ) + ", ".join(
            ['"{title}"'.format(title=source.title_text_display) for source in sources]
        )

    def handle_report_frequency(self, config, **kwargs):
        new_schedule = config.get_frequency_display()
        return _(
            "Successfully updated reporting frequency. They will now report {new_schedule} starting on {schedule_start}"
        ).format(new_schedule=new_schedule, schedule_start=config.schedule_start)

    def handle_skipped_report(self, report, **kwargs):
        if report.skipped:
            return _(
                "Successfully skipped a Report for {start_date} to {end_date}"
            ).format(start_date=report.start_date, end_date=report.end_date)
        else:
            return _(
                "Successfully unskipped a Report for {start_date} to {end_date}"
            ).format(start_date=report.start_date, end_date=report.end_date)

    def batch_transition(self, sources, transitions, **kwargs):
        base_message = "Successfully updated:"
        transition = "{submission} [{old_display} → {new_display}]."
        transition_messages = [
            transition.format(
                submission=submission.title_text_display,
                old_display=transitions[submission.id],
                new_display=submission.phase,
            )
            for submission in sources
        ]
        messages = [base_message, *transition_messages]
        return " ".join(messages)

    def batch_determinations(self, sources, determinations, **kwargs):
        submissions = sources
        outcome = determinations[submissions[0].id].clean_outcome

        base_message = _("Successfully determined as {outcome}: ").format(
            outcome=outcome
        )
        submissions_text = [submission.title_text_display for submission in submissions]
        return base_message + ", ".join(submissions_text)

    def recipients(self, *args, **kwargs):
        return [None]

    def batch_recipients(self, message_type, sources, *args, **kwargs):
        return [
            {
                "recipients": [None],
                "sources": sources,
            }
        ]

    def send_message(self, message, request, **kwargs):
        messages.add_message(request, messages.INFO, message)
