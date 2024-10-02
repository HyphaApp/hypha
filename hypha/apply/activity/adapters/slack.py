import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from django_slack import slack_message

from hypha.apply.activity.adapters.base import AdapterBase
from hypha.apply.activity.adapters.utils import link_to, reviewers_message
from hypha.apply.activity.options import MESSAGES
from hypha.apply.projects.models.payment import (
    APPROVED_BY_STAFF,
    CHANGES_REQUESTED_BY_FINANCE,
    PAID,
    PAYMENT_FAILED,
    RESUBMITTED,
    SUBMITTED,
)

logger = logging.getLogger(__name__)
User = get_user_model()


class SlackAdapter(AdapterBase):
    """Notification Adaptor for internal staff on the configured slack channels."""

    adapter_type = "Slack"
    always_send = True
    messages = {
        MESSAGES.NEW_SUBMISSION: _(
            "A new submission has been submitted for {source.page.title}: <{link}|{source.title_text_display}> by {user}"
        ),
        MESSAGES.UPDATE_LEAD: _(
            "The lead of <{link}|{source.title_text_display}> has been updated from {old_lead} to {source.lead} by {user}"
        ),
        MESSAGES.BATCH_UPDATE_LEAD: "handle_batch_lead",
        MESSAGES.COMMENT: _(
            "A new {comment.visibility} comment has been posted on <{link}|{source.title}> by {user}"
        ),
        MESSAGES.EDIT_SUBMISSION: _(
            "{user} has edited <{link}|{source.title_text_display}>"
        ),
        MESSAGES.APPLICANT_EDIT: _(
            "{user} has edited <{link}|{source.title_text_display}>"
        ),
        MESSAGES.REVIEWERS_UPDATED: "reviewers_updated",
        MESSAGES.BATCH_REVIEWERS_UPDATED: "handle_batch_reviewers",
        MESSAGES.PARTNERS_UPDATED: _(
            "{user} has updated the partners on <{link}|{source.title_text_display}>"
        ),
        MESSAGES.TRANSITION: _(
            "{user} has updated the status of <{link}|{source.title_text_display}>: {old_phase.display_name} → {source.phase}"
        ),
        MESSAGES.BATCH_TRANSITION: "handle_batch_transition",
        MESSAGES.DETERMINATION_OUTCOME: "handle_determination",
        MESSAGES.BATCH_DETERMINATION_OUTCOME: "handle_batch_determination",
        MESSAGES.PROPOSAL_SUBMITTED: _(
            "A proposal has been submitted for review: <{link}|{source.title_text_display}>"
        ),
        MESSAGES.INVITED_TO_PROPOSAL: _(
            "<{link}|{source.title_text_display}> by {source.user} has been invited to submit a proposal"
        ),
        MESSAGES.NEW_REVIEW: _(
            "{user} has submitted a review for <{link}|{source.title_text_display}>. Outcome: {review.outcome},  Score: {review.get_score_display}"
        ),
        MESSAGES.READY_FOR_REVIEW: "notify_reviewers",
        MESSAGES.OPENED_SEALED: _(
            "{user} has opened the sealed submission: <{link}|{source.title_text_display}>"
        ),
        MESSAGES.REVIEW_OPINION: _(
            "{user} {opinion.opinion_display}s with {opinion.review.author}s review of <{link}|{source.title_text_display}>"
        ),
        MESSAGES.BATCH_READY_FOR_REVIEW: "batch_notify_reviewers",
        MESSAGES.DELETE_SUBMISSION: _("{user} has deleted {source.title_text_display}"),
        MESSAGES.DELETE_REVIEW: _(
            "{user} has deleted {review.author} review for <{link}|{source.title_text_display}>"
        ),
        MESSAGES.DELETE_REVIEW_OPINION: _(
            "{user} has deleted {review_opinion.author} review opinion for <{link}|{source.title_text_display}>"
        ),
        MESSAGES.CREATED_PROJECT: _(
            "{user} has created a Project: <{link}|{source.title}>"
        ),
        MESSAGES.UPDATE_PROJECT_LEAD: _(
            "The lead of project <{link}|{source.title}> has been updated from {old_lead} to {source.lead} by {user}"
        ),
        MESSAGES.UPDATE_PROJECT_TITLE: _(
            "The project title has been updated from <{link}|{old_title}> to <{link}|{source.title}> by {user}"
        ),
        MESSAGES.EDIT_REVIEW: _(
            "{user} has edited {review.author} review for <{link}|{source.title_text_display}>"
        ),
        MESSAGES.SEND_FOR_APPROVAL: _(
            "{user} has requested approval on project <{link}|{source.title}>"
        ),
        MESSAGES.APPROVE_PROJECT: _(
            "{user} has approved project <{link}|{source.title}>"
        ),
        MESSAGES.REQUEST_PROJECT_CHANGE: _(
            "{user} has requested changes for project acceptance on <{link}|{source.title}>"
        ),
        MESSAGES.UPLOAD_CONTRACT: _(
            "{user} has uploaded a contract for <{link}|{source.title}>"
        ),
        MESSAGES.SUBMIT_CONTRACT_DOCUMENTS: _(
            "{user} has submitted the contracting document for project <{link}|{source.title}>"
        ),
        MESSAGES.APPROVE_CONTRACT: _(
            "{user} has approved contract for <{link}|{source.title}>"
        ),
        MESSAGES.CREATE_INVOICE: _(
            "{user} has created invoice for <{link}|{source.title}>"
        ),
        MESSAGES.UPDATE_INVOICE_STATUS: _(
            "{user} has changed the status of <{link_related}|invoice> on <{link}|{source.title}> to {invoice.status_display}"
        ),
        MESSAGES.DELETE_INVOICE: _(
            "{user} has deleted invoice from <{link}|{source.title}>"
        ),
        MESSAGES.UPDATE_INVOICE: _(
            "{user} has updated invoice for <{link}|{source.title}>"
        ),
        MESSAGES.SUBMIT_REPORT: _(
            "{user} has submitted a report for <{link}|{source.title}>"
        ),
        MESSAGES.BATCH_DELETE_SUBMISSION: "handle_batch_delete_submission",
        MESSAGES.STAFF_ACCOUNT_CREATED: _(
            "{user} has created a new account for <{link}|{source}>"
        ),
        MESSAGES.STAFF_ACCOUNT_EDITED: _(
            "{user} has edited account for <{link}|{source}> that now has following roles: {roles}"
        ),
        MESSAGES.BATCH_ARCHIVE_SUBMISSION: "handle_batch_archive_submission",
        MESSAGES.ARCHIVE_SUBMISSION: _(
            "{user} has archived the submission: {source.title_text_display}"
        ),
        MESSAGES.UNARCHIVE_SUBMISSION: _(
            "{user} has unarchived the submission: {source.title_text_display}"
        ),
    }

    def __init__(self):
        super().__init__()
        self.destination = settings.SLACK_ENDPOINT_URL
        self.target_room = settings.SLACK_DESTINATION_ROOM
        self.comments_room = settings.SLACK_DESTINATION_ROOM_COMMENTS
        self.comments_type = settings.SLACK_TYPE_COMMENTS

    def slack_links(self, links, sources):
        return ", ".join(
            f"<{links[source.id]}|{getattr(source, 'title_text_display', source.title)}>"
            for source in sources
        )

    def extra_kwargs(self, message_type, **kwargs):
        source = kwargs["source"]
        sources = kwargs["sources"]
        request = kwargs["request"]
        related = kwargs["related"]
        link = link_to(source, request)
        link_related = link_to(related, request)
        links = {source.id: link_to(source, request) for source in sources}
        return {
            "link": link,
            "link_related": link_related,
            "links": links,
        }

    def recipients(self, message_type, source, related, **kwargs):
        if message_type in [
            MESSAGES.STAFF_ACCOUNT_CREATED,
            MESSAGES.STAFF_ACCOUNT_EDITED,
        ]:
            return [self.slack_id(kwargs["user"])]

        if message_type == MESSAGES.SEND_FOR_APPROVAL:
            return [
                self.slack_id(user)
                for user in User.objects.approvers()
                if self.slack_id(user)
            ]

        recipients = [self.slack_id(source.lead)]
        # Notify second reviewer when first reviewer is done.
        if message_type in [MESSAGES.NEW_REVIEW, MESSAGES.REVIEW_OPINION] and related:
            submission = source
            role_reviewers = [
                role_reviewer.reviewer
                for role_reviewer in submission.assigned.with_roles()
            ]
            if related.author.reviewer in role_reviewers:
                for reviewer in role_reviewers:
                    if reviewer != related.author.reviewer:
                        recipients.append(self.slack_id(reviewer))

        if message_type == MESSAGES.UPDATE_INVOICE_STATUS:
            if related.status in [
                SUBMITTED,
                RESUBMITTED,
                CHANGES_REQUESTED_BY_FINANCE,
                PAID,
                PAYMENT_FAILED,
            ]:
                # Notify project lead/staff
                return recipients
            if related.status in [APPROVED_BY_STAFF]:
                # Notify finance 1
                return [
                    self.slack_id(user)
                    for user in User.objects.finances()
                    if self.slack_id(user)
                ]
            return []
        return recipients

    def batch_recipients(self, message_type, sources, **kwargs):
        # We group the messages by lead
        leads = User.objects.filter(id__in=sources.values("lead"))
        return [
            {
                "recipients": [self.slack_id(lead)],
                "sources": sources.filter(lead=lead),
            }
            for lead in leads
        ]

    def reviewers_updated(self, source, link, user, added=None, removed=None, **kwargs):
        if added is None:
            added = []
        if removed is None:
            removed = []
        submission = source
        message = [
            _("{user} has updated the reviewers on <{link}|{title}>").format(
                user=user, link=link, title=submission.title_text_display
            )
        ]

        if added:
            message.append(_("Added:"))
            message.extend(reviewers_message(added))

        if removed:
            message.append(_("Removed:"))
            message.extend(reviewers_message(removed))

        return " ".join(message)

    def handle_batch_lead(self, sources, links, user, new_lead, **kwargs):
        submissions = sources
        submissions_text = self.slack_links(links, submissions)
        return _(
            "{user} has batch changed lead to {new_lead} on: {submissions_text}"
        ).format(
            user=user,
            submissions_text=submissions_text,
            new_lead=new_lead,
        )

    def handle_batch_reviewers(self, sources, links, user, added, **kwargs):
        submissions = sources
        submissions_text = self.slack_links(links, submissions)
        reviewers_text = " ".join(
            [
                _("{user} as {name},").format(user=str(user), name=role.name)
                for role, user in added
                if user
            ]
        )
        return _(
            "{user} has batch added {reviewers_text} as reviewers on: {submissions_text}"
        ).format(
            user=user,
            submissions_text=submissions_text,
            reviewers_text=reviewers_text,
        )

    def handle_batch_transition(self, user, links, sources, transitions, **kwargs):
        submissions = sources
        submissions_text = [
            ": ".join(
                [
                    self.slack_links(links, [submission]),
                    f"{transitions[submission.id].display_name} → {submission.phase}",
                ]
            )
            for submission in submissions
        ]
        submissions_links = ",".join(submissions_text)
        return _(
            "{user} has transitioned the following submissions: {submissions_links}"
        ).format(
            user=user,
            submissions_links=submissions_links,
        )

    def handle_determination(self, source, link, determination, **kwargs):
        submission = source
        if determination.send_notice:
            return _(
                "A determination for <{link}|{submission_title}> was sent by email. Outcome: {determination_outcome}"
            ).format(
                link=link,
                submission_title=submission.title_text_display,
                determination_outcome=determination.clean_outcome,
            )
        return _(
            "A determination for <{link}|{submission_title}> was saved without sending an email. Outcome: {determination_outcome}"
        ).format(
            link=link,
            submission_title=submission.title_text_display,
            determination_outcome=determination.clean_outcome,
        )

    def handle_batch_determination(self, sources, links, determinations, **kwargs):
        submissions = sources
        submissions_links = ",".join(
            [self.slack_links(links, [submission]) for submission in submissions]
        )

        outcome = determinations[submissions[0].id].clean_outcome

        return _(
            "Determinations of {outcome} was sent for: {submissions_links}"
        ).format(
            outcome=outcome,
            submissions_links=submissions_links,
        )

    def handle_batch_delete_submission(self, sources, links, user, **kwargs):
        submissions = sources
        submissions_text = ", ".join(
            [submission.title_text_display for submission in submissions]
        )
        return _("{user} has deleted submissions: {title}").format(
            user=user, title=submissions_text
        )

    def handle_batch_archive_submission(self, sources, links, user, **kwargs):
        submissions = sources
        submissions_text = ", ".join([submission.title for submission in submissions])
        return _("{user} has archived submissions: {title}").format(
            user=user, title=submissions_text
        )

    def notify_reviewers(self, source, link, **kwargs):
        submission = source
        reviewers_to_notify = []
        for reviewer in submission.reviewers.all():
            if submission.phase.permissions.can_review(reviewer):
                reviewers_to_notify.append(reviewer)

        reviewers = ", ".join(str(reviewer) for reviewer in reviewers_to_notify)

        return _(
            "<{link}|{title}> is ready for review. The following are assigned as reviewers: {reviewers}"
        ).format(
            link=link,
            reviewers=reviewers,
            title=submission.title_text_display,
        )

    def batch_notify_reviewers(self, sources, links, **kwargs):
        kwargs.pop("source")
        kwargs.pop("link")
        return ". ".join(
            self.notify_reviewers(source, link=links[source.id], **kwargs)
            for source in sources
        )

    def slack_id(self, user):
        if user is None:
            return ""

        if not user.slack:
            return ""

        return f"<{user.slack}>"

    def slack_channels(self, source, **kwargs):
        # Set the default room as a start.
        target_rooms = [self.target_room]
        try:
            fund_slack_channel = source.get_from_parent("slack_channel").split(",")
        except AttributeError:
            # Not a submission object.
            pass
        else:
            # If there are custom rooms, set them in place of the default room
            custom_rooms = [channel for channel in fund_slack_channel if channel]
            if len(custom_rooms) > 0:
                target_rooms = custom_rooms

        try:
            comment = kwargs["comment"]
        except KeyError:
            # Not a comment, no extra rooms.
            pass
        else:
            if self.comments_room:
                if any(self.comments_type):
                    if comment.visibility in self.comments_type:
                        target_rooms.extend([self.comments_room])
                else:
                    target_rooms.extend([self.comments_room])

        # Make sure each channel name starts with a "#".
        target_rooms = [
            room.strip() if room.startswith("#") else "#" + room.strip()
            for room in target_rooms
            if room
        ]

        return target_rooms

    def send_message(self, message, recipient, source, **kwargs):
        target_rooms = self.slack_channels(source, **kwargs)

        if not any(target_rooms) or not settings.SLACK_TOKEN:
            errors = []
            if not target_rooms:
                errors.append("Room ID")
            if not settings.SLACK_TOKEN:
                errors.append("Slack Token")
            return "Missing configuration: {}".format(", ".join(errors))

        message = " ".join([recipient, message]).strip()

        data = {
            "message": message,
        }
        for room in target_rooms:
            try:
                slack_message("messages/slack_message.html", data, channel=room)
            except Exception as e:
                logger.exception(e)
                return "400: Bad Request"
        return "200: OK"
