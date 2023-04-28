import logging
from collections import defaultdict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from hypha.apply.projects.models.payment import CHANGES_REQUESTED_BY_STAFF, DECLINED
from hypha.apply.users.groups import (
    APPROVER_GROUP_NAME,
    CONTRACTING_GROUP_NAME,
    FINANCE_GROUP_NAME,
    STAFF_GROUP_NAME,
)
from hypha.apply.users.models import User
from hypha.core.mail import (
    language,
    remove_extra_empty_lines,
)

from ..options import MESSAGES
from ..tasks import send_mail
from .base import AdapterBase
from .utils import (
    get_compliance_email,
    is_ready_for_review,
    is_reviewer_update,
    is_transition,
)

logger = logging.getLogger(__name__)


class EmailAdapter(AdapterBase):
    adapter_type = 'Email'
    messages = {
        MESSAGES.NEW_SUBMISSION: 'messages/email/submission_confirmation.html',
        MESSAGES.DRAFT_SUBMISSION: 'messages/email/submission_confirmation.html',
        MESSAGES.COMMENT: 'notify_comment',
        MESSAGES.EDIT_SUBMISSION: 'messages/email/submission_edit.html',
        MESSAGES.TRANSITION: 'handle_transition',
        MESSAGES.BATCH_TRANSITION: 'handle_batch_transition',
        MESSAGES.DETERMINATION_OUTCOME: 'handle_determination',
        MESSAGES.BATCH_DETERMINATION_OUTCOME: 'handle_batch_determination',
        MESSAGES.INVITED_TO_PROPOSAL: 'messages/email/invited_to_proposal.html',
        MESSAGES.BATCH_READY_FOR_REVIEW: 'handle_batch_ready_for_review',
        MESSAGES.READY_FOR_REVIEW: 'handle_ready_for_review',
        MESSAGES.REVIEWERS_UPDATED: 'handle_ready_for_review',
        MESSAGES.BATCH_REVIEWERS_UPDATED: 'handle_batch_ready_for_review',
        MESSAGES.PARTNERS_UPDATED: 'partners_updated_applicant',
        MESSAGES.PARTNERS_UPDATED_PARTNER: 'partners_updated_partner',
        MESSAGES.UPLOAD_CONTRACT: 'messages/email/contract_uploaded.html',
        MESSAGES.SUBMIT_CONTRACT_DOCUMENTS: 'messages/email/submit_contract_documents.html',
        MESSAGES.CREATED_PROJECT: 'handle_project_created',
        MESSAGES.UPDATED_VENDOR: 'handle_vendor_updated',
        MESSAGES.SENT_TO_COMPLIANCE: 'messages/email/sent_to_compliance.html',
        MESSAGES.SEND_FOR_APPROVAL: 'messages/email/paf_for_approval.html',
        MESSAGES.REQUEST_PROJECT_CHANGE: 'messages/email/project_request_change.html',
        MESSAGES.APPROVE_PAF: 'messages/email/paf_for_approval.html',
        MESSAGES.UPDATE_INVOICE: 'handle_invoice_updated',
        MESSAGES.UPDATE_INVOICE_STATUS: 'handle_invoice_status_updated',
        MESSAGES.APPROVE_INVOICE: 'messages/email/invoice_approved.html',
        MESSAGES.SUBMIT_REPORT: 'messages/email/report_submitted.html',
        MESSAGES.SKIPPED_REPORT: 'messages/email/report_skipped.html',
        MESSAGES.REPORT_FREQUENCY_CHANGED: 'messages/email/report_frequency.html',
        MESSAGES.REPORT_NOTIFY: 'messages/email/report_notify.html',
        MESSAGES.REVIEW_REMINDER: 'messages/email/ready_to_review.html',
        MESSAGES.PROJECT_TRANSITION: 'handle_project_transition',
    }

    def get_subject(self, message_type, source):
        if source and hasattr(source, 'title'):
            if is_ready_for_review(message_type) or is_reviewer_update(message_type):
                subject = _('Application ready to review: {source.title}').format(
                    source=source
                )
                if message_type in {
                    MESSAGES.BATCH_READY_FOR_REVIEW,
                    MESSAGES.BATCH_REVIEWERS_UPDATED,
                }:
                    subject = _('Multiple applications are now ready for your review')
            elif message_type in {MESSAGES.REVIEW_REMINDER}:
                subject = _(
                    'Reminder: Application ready to review: {source.title}'
                ).format(source=source)
            elif message_type in [MESSAGES.SENT_TO_COMPLIANCE]:
                subject = _('Project is waiting for approval: {source.title}').format(source=source)
            elif message_type == MESSAGES.UPLOAD_CONTRACT:
                subject = _('Contract uploaded for the project: {source.title}').format(source=source)
            elif message_type == MESSAGES.SUBMIT_CONTRACT_DOCUMENTS:
                subject = _('Contract Documents required approval for the project: {source.title}').format(source=source)
            elif message_type == MESSAGES.PROJECT_TRANSITION:
                from hypha.apply.projects.models.project import CONTRACTING, IN_PROGRESS
                if source.status == CONTRACTING:
                    subject = _('Project is waiting for the contract: {source.title}').format(source=source)
                elif source.status == IN_PROGRESS:
                    subject = _('Project is ready for invoicing: {source.title}').format(source=source)
                else:
                    subject = _('Project status has changed to {source.status}: {source.title}').format(source=source)
            elif message_type == MESSAGES.REQUEST_PROJECT_CHANGE:
                subject = _("Project has been rejected, please update and resubmit")
            else:
                try:
                    subject = source.page.specific.subject or _(
                        'Your application to {org_long_name}: {source.title}'
                    ).format(org_long_name=settings.ORG_LONG_NAME, source=source)
                except AttributeError:
                    subject = _('Your {org_long_name} Project: {source.title}').format(
                        org_long_name=settings.ORG_LONG_NAME, source=source
                    )
            return subject

    def extra_kwargs(self, message_type, source, sources, **kwargs):
        return {
            'subject': self.get_subject(message_type, source),
        }

    def handle_transition(self, old_phase, source, **kwargs):
        from hypha.apply.funds.workflow import PHASES

        submission = source
        # Retrive status index to see if we are going forward or backward.
        old_index = list(dict(PHASES).keys()).index(old_phase.name)
        target_index = list(dict(PHASES).keys()).index(submission.status)
        is_forward = old_index < target_index

        if is_forward:
            return self.render_message(
                'messages/email/transition.html',
                source=submission,
                old_phase=old_phase,
                **kwargs,
            )

    def handle_batch_transition(self, transitions, sources, **kwargs):
        submissions = sources
        kwargs.pop('source')
        for submission in submissions:
            old_phase = transitions[submission.id]
            return self.handle_transition(
                old_phase=old_phase, source=submission, **kwargs
            )

    def handle_project_transition(self, source, **kwargs):
        from hypha.apply.projects.models.project import CONTRACTING, IN_PROGRESS
        if source.status == CONTRACTING:
            return self.render_message(
                'messages/email/ready_for_contracting.html',
                source=source,
                **kwargs,
            )

        if source.status == IN_PROGRESS:
            return self.render_message(
                'messages/email/ready_for_invoicing.html',
                source=source,
                **kwargs,
            )

    def handle_invoice_status_updated(self, related, **kwargs):
        return self.render_message(
            'messages/email/invoice_status_updated.html',
            has_changes_requested=related.has_changes_requested,
            **kwargs,
        )

    def handle_invoice_updated(self, **kwargs):
        return self.render_message(
            'messages/email/invoice_updated.html',
            **kwargs,
        )

    def handle_project_created(self, source, **kwargs):
        from hypha.apply.projects.models import ProjectSettings

        request = kwargs.get('request')
        project_settings = ProjectSettings.for_request(request)
        if project_settings.vendor_setup_required:
            return self.render_message(
                'messages/email/vendor_setup_needed.html', source=source, **kwargs
            )

    def handle_vendor_updated(self, source, **kwargs):
        return self.render_message(
            'messages/email/vendor_updated.html',
            source=source,
            **kwargs,
        )

    def handle_determination(self, determination, source, **kwargs):
        submission = source
        if determination.send_notice:
            return self.render_message(
                'messages/email/determination.html',
                source=submission,
                determination=determination,
                **kwargs,
            )

    def handle_batch_determination(self, determinations, sources, **kwargs):
        submissions = sources
        kwargs.pop('source')
        for submission in submissions:
            determination = determinations[submission.id]
            return self.render_message(
                'messages/email/determination.html',
                source=submission,
                determination=determination,
                **kwargs,
            )

    def handle_ready_for_review(self, request, source, **kwargs):
        if settings.SEND_READY_FOR_REVIEW:
            return self.render_message(
                'messages/email/ready_to_review.html',
                source=source,
                request=request,
                **kwargs,
            )

    def handle_batch_ready_for_review(self, request, sources, **kwargs):
        if settings.SEND_READY_FOR_REVIEW:
            return self.render_message(
                'messages/email/batch_ready_to_review.html',
                sources=sources,
                request=request,
                **kwargs,
            )

    def notify_comment(self, **kwargs):
        comment = kwargs['comment']
        source = kwargs['source']
        if not comment.priviledged and not comment.user == source.user:
            return self.render_message('messages/email/comment.html', **kwargs)

    def recipients(self, message_type, source, user, **kwargs):
        if is_ready_for_review(message_type):
            return self.reviewers(source)

        if is_reviewer_update(message_type):
            # Notify newly added reviewers only if they can review in the current phase
            reviewers = self.reviewers(source)
            added = kwargs.get("added", [])
            return [
                assigned_reviewer.reviewer.email
                for assigned_reviewer in added
                if assigned_reviewer.reviewer.email in reviewers
            ]

        if is_transition(message_type):
            # Only notify the applicant if the new phase can be seen within the workflow
            if not source.phase.permissions.can_view(source.user):
                return []

        if message_type == MESSAGES.PARTNERS_UPDATED_PARTNER:
            partners = kwargs['added']
            return [partner.email for partner in partners]

        if message_type in [MESSAGES.SEND_FOR_APPROVAL, MESSAGES.APPROVE_PAF]:
            from hypha.apply.projects.models.project import ProjectSettings
            # notify the assigned approvers
            request = kwargs.get('request')
            project_settings = ProjectSettings.for_request(request)
            if project_settings.paf_approval_sequential:
                next_paf_approval = source.paf_approvals.filter(approved=False).first()
                if next_paf_approval:
                    return [next_paf_approval.user.email]
            return source.paf_approvals.filter(approved=False).values_list('user__email', flat=True)

        if message_type == MESSAGES.REQUEST_PROJECT_CHANGE:
            return [source.lead.email]

        if message_type == MESSAGES.SENT_TO_COMPLIANCE:
            return get_compliance_email(target_user_gps=[CONTRACTING_GROUP_NAME, FINANCE_GROUP_NAME, STAFF_GROUP_NAME])

        if message_type == MESSAGES.SUBMIT_CONTRACT_DOCUMENTS:
            return get_compliance_email(target_user_gps=[STAFF_GROUP_NAME])

        if message_type in {MESSAGES.SUBMIT_REPORT, MESSAGES.UPDATE_INVOICE}:
            # Don't tell the user if they did these activities
            if user.is_applicant:
                return []

        if message_type in {MESSAGES.REVIEW_REMINDER}:
            return self.reviewers(source)

        if message_type == MESSAGES.UPDATE_INVOICE_STATUS:
            related = kwargs.get('related', None)
            if related:
                if related.status in {CHANGES_REQUESTED_BY_STAFF, DECLINED}:
                    return [source.user.email]
            return []

        if message_type == MESSAGES.PROJECT_TRANSITION:
            from hypha.apply.projects.models.project import CONTRACTING, IN_PROGRESS
            if source.status == CONTRACTING:
                return get_compliance_email(target_user_gps=[CONTRACTING_GROUP_NAME])
            if source.status == IN_PROGRESS:
                return [source.user.email]

        if message_type == MESSAGES.APPROVE_INVOICE:
            if user.is_apply_staff:
                return get_compliance_email(target_user_gps=[FINANCE_GROUP_NAME])
            if settings.INVOICE_EXTENDED_WORKFLOW and user.is_finance_level_1:
                finance_2_users_email = User.objects.filter(groups__name=FINANCE_GROUP_NAME).\
                    filter(groups__name=APPROVER_GROUP_NAME).values_list('email', flat=True)
                return finance_2_users_email
            return []

        if isinstance(source, get_user_model()):
            return user.email
        return [source.user.email]

    def batch_recipients(self, message_type, sources, **kwargs):
        if not (is_ready_for_review(message_type) or is_reviewer_update(message_type)):
            return super().batch_recipients(message_type, sources, **kwargs)

        added = [reviewer.email for _, reviewer in kwargs.get("added", []) if reviewer]

        reviewers_to_message = defaultdict(list)
        for source in sources:
            reviewers = self.reviewers(source)
            for reviewer in reviewers:
                if not is_reviewer_update(message_type) or reviewer in added:
                    reviewers_to_message[reviewer].append(source)

        return [
            {
                'recipients': [reviewer],
                'sources': sources,
            }
            for reviewer, sources in reviewers_to_message.items()
        ]

    def reviewers(self, source):
        return [
            reviewer.email
            for reviewer in source.missing_reviewers.all()
            if source.phase.permissions.can_review(reviewer)
            and not reviewer.is_apply_staff
        ]

    def partners_updated_applicant(self, added, removed, **kwargs):
        if added:
            return self.render_message(
                'messages/email/partners_update_applicant.html', added=added, **kwargs
            )

    def partners_updated_partner(self, added, removed, **kwargs):
        for _partner in added:
            return self.render_message(
                'messages/email/partners_update_partner.html', **kwargs
            )

    def render_message(self, template, **kwargs):

        with language(settings.LANGUAGE_CODE):
            text = render_to_string(template, kwargs, kwargs['request'])

        return remove_extra_empty_lines(text)

    def send_message(self, message, source, subject, recipient, logs, **kwargs):
        try:
            from_email = source.page.specific.from_address
        except AttributeError:  # we're dealing with a project
            from_email = source.submission.page.specific.from_address
        except Exception as e:
            from_email = None
            logger.exception(e)

        try:
            send_mail(subject, message, from_email, [recipient], logs=logs)
        except Exception as e:
            return 'Error: ' + str(e)
