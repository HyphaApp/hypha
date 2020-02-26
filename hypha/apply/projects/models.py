import collections
import datetime
import decimal
import json
import logging
import os

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.humanize.templatetags.humanize import ordinal
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import (
    Case,
    Count,
    ExpressionWrapper,
    F,
    Max,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Cast, Coalesce
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.core.fields import StreamField

from addressfield.fields import ADDRESS_FIELDS_ORDER
from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.funds.models.mixins import AccessFormData
from hypha.apply.stream_forms.blocks import FormFieldsBlock
from hypha.apply.stream_forms.files import StreamFieldDataEncoder
from hypha.apply.stream_forms.models import BaseStreamForm
from hypha.apply.utils.storage import PrivateStorage

logger = logging.getLogger(__name__)


def contract_path(instance, filename):
    return f'projects/{instance.project_id}/contracts/{filename}'


def document_path(instance, filename):
    return f'projects/{instance.project_id}/supporting_documents/{filename}'


def invoice_path(instance, filename):
    return f'projects/{instance.project_id}/payment_invoices/{filename}'


def receipt_path(instance, filename):
    return f'projects/{instance.payment_request.project_id}/payment_receipts/{filename}'


def report_path(instance, filename):
    return f'reports/{instance.report.report_id}/version/{instance.report_id}/{filename}'


class Approval(models.Model):
    project = models.ForeignKey("Project", on_delete=models.CASCADE, related_name="approvals")
    by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="approvals")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['project', 'by']

    def __str__(self):
        return f'Approval of "{self.project.title}" by {self.by}'


class ContractQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(is_signed=True, approver__isnull=False)


class Contract(models.Model):
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='contracts')
    project = models.ForeignKey("Project", on_delete=models.CASCADE, related_name="contracts")

    file = models.FileField(upload_to=contract_path, storage=PrivateStorage())

    is_signed = models.BooleanField("Signed?", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True)

    objects = ContractQuerySet.as_manager()

    @property
    def state(self):
        return 'Signed' if self.is_signed else 'Unsigned'

    def __str__(self):
        return f'Contract for {self.project} ({self.state})'

    def get_absolute_url(self):
        return reverse('apply:projects:contract', args=[self.project.pk, self.pk])


class PacketFile(models.Model):
    category = models.ForeignKey("DocumentCategory", null=True, on_delete=models.CASCADE, related_name="packet_files")
    project = models.ForeignKey("Project", on_delete=models.CASCADE, related_name="packet_files")

    title = models.TextField()
    document = models.FileField(upload_to=document_path, storage=PrivateStorage())

    def __str__(self):
        return f'Project file: {self.title}'

    def get_remove_form(self):
        """
        Get an instantiated RemoveDocumentForm with this class as `instance`.

        This allows us to build instances of the RemoveDocumentForm for each
        instance of PacketFile in the supporting documents template.  The
        standard Delegated View flow makes it difficult to create these forms
        in the view or template.
       """
        from .forms import RemoveDocumentForm
        return RemoveDocumentForm(instance=self)


@receiver(post_delete, sender=PacketFile)
def delete_packetfile_file(sender, instance, **kwargs):
    # Remove the file and don't save the base model
    instance.document.delete(False)


class PaymentApproval(models.Model):
    request = models.ForeignKey('PaymentRequest', on_delete=models.CASCADE, related_name="approvals")
    by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_approvals")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Approval for {self.request} by {self.by}'


class PaymentReceipt(models.Model):
    payment_request = models.ForeignKey("PaymentRequest", on_delete=models.CASCADE, related_name="receipts")

    file = models.FileField(upload_to=receipt_path, storage=PrivateStorage())

    def __str__(self):
        return os.path.basename(self.file.name)


SUBMITTED = 'submitted'
CHANGES_REQUESTED = 'changes_requested'
UNDER_REVIEW = 'under_review'
PAID = 'paid'
DECLINED = 'declined'
REQUEST_STATUS_CHOICES = [
    (SUBMITTED, 'Submitted'),
    (CHANGES_REQUESTED, 'Changes Requested'),
    (UNDER_REVIEW, 'Under Review'),
    (PAID, 'Paid'),
    (DECLINED, 'Declined'),
]


class PaymentRequestQueryset(models.QuerySet):
    def in_progress(self):
        return self.exclude(status__in=[DECLINED, PAID])

    def rejected(self):
        return self.filter(status=DECLINED)

    def not_rejected(self):
        return self.exclude(status=DECLINED)

    def total_value(self, field):
        return self.aggregate(total=Coalesce(Sum(field), Value(0)))['total']

    def paid_value(self):
        return self.filter(status=PAID).total_value('paid_value')

    def unpaid_value(self):
        return self.filter(status__in=[SUBMITTED, UNDER_REVIEW]).total_value('requested_value')


class PaymentRequest(models.Model):
    project = models.ForeignKey("Project", on_delete=models.CASCADE, related_name="payment_requests")
    by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_requests")

    requested_value = models.DecimalField(
        default=0,
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(decimal.Decimal('0.01'))],
    )
    paid_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(decimal.Decimal('0.01'))],
        null=True
    )

    invoice = models.FileField(upload_to=invoice_path, storage=PrivateStorage())
    requested_at = models.DateTimeField(auto_now_add=True)
    date_from = models.DateTimeField()
    date_to = models.DateTimeField()
    comment = models.TextField(blank=True)
    status = models.TextField(choices=REQUEST_STATUS_CHOICES, default=SUBMITTED)

    objects = PaymentRequestQueryset.as_manager()

    def __str__(self):
        return f'Payment requested for {self.project}'

    @property
    def has_changes_requested(self):
        return self.status == CHANGES_REQUESTED

    @property
    def status_display(self):
        return self.get_status_display()

    def can_user_delete(self, user):
        if user.is_applicant:
            if self.status in (SUBMITTED, CHANGES_REQUESTED):
                return True

        if user.is_apply_staff:
            if self.status in {SUBMITTED}:
                return True

        return False

    def can_user_edit(self, user):
        if user.is_applicant:
            if self.status in {SUBMITTED, CHANGES_REQUESTED}:
                return True

        if user.is_apply_staff:
            if self.status in {SUBMITTED}:
                return True

        return False

    def can_user_change_status(self, user):
        if not user.is_apply_staff:
            return False  # Users can't change status

        if self.status in {PAID, DECLINED}:
            return False

        return True

    @property
    def value(self):
        return self.paid_value or self.requested_value

    def get_absolute_url(self):
        return reverse('apply:projects:payments:detail', args=[self.pk])


COMMITTED = 'committed'
CONTRACTING = 'contracting'
IN_PROGRESS = 'in_progress'
CLOSING = 'closing'
COMPLETE = 'complete'
PROJECT_STATUS_CHOICES = [
    (COMMITTED, 'Committed'),
    (CONTRACTING, 'Contracting'),
    (IN_PROGRESS, 'In Progress'),
    (CLOSING, 'Closing'),
    (COMPLETE, 'Complete'),
]


class ProjectQuerySet(models.QuerySet):
    def active(self):
        "Projects that are not finished"
        return self.exclude(status=COMPLETE)

    def in_progress(self):
        "Projects that users need to interact with, submitting reports or payment request"
        return self.filter(
            status__in=(IN_PROGRESS, CLOSING,)
        )

    def complete(self):
        return self.filter(status=COMPLETE)

    def in_approval(self):
        return self.filter(
            is_locked=True,
            status=COMMITTED,
            approvals__isnull=True,
        )

    def by_end_date(self, desc=False):
        order = getattr(F('proposed_end'), 'desc' if desc else 'asc')(nulls_last=True)

        return self.order_by(order)

    def with_amount_paid(self):
        return self.annotate(
            amount_paid=Coalesce(Sum('payment_requests__paid_value'), Value(0)),
        )

    def with_last_payment(self):
        return self.annotate(
            last_payment_request=Max('payment_requests__requested_at'),
        )

    def with_outstanding_reports(self):
        return self.annotate(
            outstanding_reports=Subquery(
                Report.objects.filter(
                    project=OuterRef('pk'),
                ).to_do().order_by().values('project').annotate(
                    count=Count('pk'),
                ).values('count'),
                output_field=models.IntegerField(),
            )
        )

    def with_start_date(self):
        return self.annotate(
            start=Cast(
                Subquery(
                    Contract.objects.filter(
                        project=OuterRef('pk'),
                    ).approved().order_by(
                        'approved_at'
                    ).values('approved_at')[:1]
                ),
                models.DateField(),
            )
        )

    def for_table(self):
        return self.with_amount_paid().with_last_payment().with_outstanding_reports().select_related(
            'report_config',
            'submission__page',
            'lead',
        )


class Project(BaseStreamForm, AccessFormData, models.Model):
    lead = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='lead_projects')
    submission = models.OneToOneField("funds.ApplicationSubmission", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='owned_projects')

    title = models.TextField()

    contact_legal_name = models.TextField(_('Person or Organisation name'), default='')
    contact_email = models.TextField(_('Email'), default='')
    contact_address = models.TextField(_('Address'), default='')
    contact_phone = models.TextField(_('Phone'), default='')
    value = models.DecimalField(
        default=0,
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(decimal.Decimal('0.01'))],
    )
    proposed_start = models.DateTimeField(_('Proposed Start Date'), null=True)
    proposed_end = models.DateTimeField(_('Proposed End Date'), null=True)

    status = models.TextField(choices=PROJECT_STATUS_CHOICES, default=COMMITTED)

    form_data = JSONField(encoder=StreamFieldDataEncoder, default=dict)
    form_fields = StreamField(FormFieldsBlock(), null=True)

    # tracks read/write state of the Project
    is_locked = models.BooleanField(default=False)

    # tracks updates to the Projects fields via the Project Application Form.
    user_has_updated_details = models.BooleanField(default=False)

    activities = GenericRelation(
        'activity.Activity',
        content_type_field='source_content_type',
        object_id_field='source_object_id',
        related_query_name='project',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    sent_to_compliance_at = models.DateTimeField(null=True)

    objects = ProjectQuerySet.as_manager()

    def __str__(self):
        return self.title

    @property
    def status_display(self):
        return self.get_status_display()

    def get_address_display(self):
        try:
            address = json.loads(self.contact_address)
        except json.JSONDecodeError:
            return ''
        else:
            return ', '.join(
                address.get(field)
                for field in ADDRESS_FIELDS_ORDER
                if address.get(field)
            )

    @classmethod
    def create_from_submission(cls, submission):
        """
        Create a Project from the given submission.

        Returns a new Project or the given ApplicationSubmissions existing
        Project.
        """
        if not settings.PROJECTS_ENABLED:
            logging.error(f'Tried to create a Project for Submission ID={submission.id} while projects are disabled')
            return None

        # OneToOne relations on the targetted model cannot be accessed without
        # an exception when the relation doesn't exist (is None).  Since we
        # want to fail fast here, we can use hasattr instead.
        if hasattr(submission, 'project'):
            return submission.project

        return Project.objects.create(
            submission=submission,
            title=submission.title,
            user=submission.user,
            contact_email=submission.user.email,
            contact_legal_name=submission.user.full_name,
            contact_address=submission.form_data.get('address', ''),
            value=submission.form_data.get('value', 0),
        )

    @property
    def start_date(self):
        # Assume project starts when OTF are happy with the first signed contract
        first_approved_contract = self.contracts.approved().order_by('approved_at').first()
        if not first_approved_contract:
            return None

        return first_approved_contract.approved_at.date()

    @property
    def end_date(self):
        # Aiming for the proposed end date as the last day of the project
        # If still ongoing assume today is the end
        return max(
            self.proposed_end.date(),
            timezone.now().date(),
        )

    def paid_value(self):
        return self.payment_requests.paid_value()

    def unpaid_value(self):
        return self.payment_requests.unpaid_value()

    def clean(self):
        if self.proposed_start is None:
            return

        if self.proposed_end is None:
            return

        if self.proposed_start > self.proposed_end:
            raise ValidationError(_('Proposed End Date must be after Proposed Start Date'))

    def save(self, *args, **kwargs):
        creating = not self.pk

        if creating:
            files = self.extract_files()
        else:
            self.process_file_data(self.form_data)

        super().save(*args, **kwargs)

        if creating:
            self.process_file_data(files)

    def editable_by(self, user):
        if self.editable:
            return True

        # Approver can edit it when they are approving
        return user.is_approver and self.can_make_approval

    @property
    def editable(self):
        if self.status not in (CONTRACTING, COMMITTED):
            return True

        # Someone has approved the project - consider it locked while with contracting
        if self.approvals.exists():
            return False

        # Someone must lead the project to make changes
        return self.lead and not self.is_locked

    def get_absolute_url(self):
        if settings.PROJECTS_ENABLED:
            return reverse('apply:projects:detail', args=[self.id])
        return '#'

    @property
    def can_make_approval(self):
        return self.is_locked and self.status == COMMITTED

    def can_request_funding(self):
        """
        Should we show this Project's funding block?
        """
        return self.status in (CLOSING, IN_PROGRESS)

    @property
    def can_send_for_approval(self):
        """
        Wrapper to expose the pending approval state

        We don't want to expose a "Sent for Approval" state to the end User so
        we infer it from the current status being "Comitted" and the Project
        being locked.
        """
        correct_state = self.status == COMMITTED and not self.is_locked
        return correct_state and self.user_has_updated_details

    @property
    def requires_approval(self):
        return not self.approvals.exists()

    def get_missing_document_categories(self):
        """
        Get the number of documents required to meet each DocumentCategorys minimum
        """
        # Count the number of documents in each category currently
        existing_categories = DocumentCategory.objects.filter(packet_files__project=self)
        counter = collections.Counter(existing_categories)

        # Find the difference between the current count and recommended count
        for category in DocumentCategory.objects.all():
            current_count = counter[category]
            difference = category.recommended_minimum - current_count
            if difference > 0:
                yield {
                    'category': category,
                    'difference': difference,
                }

    @property
    def is_in_progress(self):
        return self.status == IN_PROGRESS

    def send_to_compliance(self, request):
        """Notify Compliance about this Project."""

        messenger(
            MESSAGES.SENT_TO_COMPLIANCE,
            request=request,
            user=request.user,
            source=self,
        )

        self.sent_to_compliance_at = timezone.now()
        self.save(update_fields=['sent_to_compliance_at'])


@register_setting
class ProjectSettings(BaseSetting):
    compliance_email = models.TextField("Compliance Email")


class DocumentCategory(models.Model):
    name = models.CharField(max_length=254)
    recommended_minimum = models.PositiveIntegerField()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'Document Categories'


class ProjectApprovalForm(BaseStreamForm, models.Model):
    name = models.CharField(max_length=255)
    form_fields = StreamField(FormFieldsBlock())

    panels = [
        FieldPanel('name'),
        StreamFieldPanel('form_fields'),
    ]

    def __str__(self):
        return self.name


class ReportConfig(models.Model):
    """Persists configuration about the reporting schedule etc"""

    WEEK = "week"
    MONTH = "month"
    FREQUENCY_CHOICES = [
        (WEEK, "Weeks"),
        (MONTH, "Months"),
    ]

    project = models.OneToOneField("Project", on_delete=models.CASCADE, related_name="report_config")
    schedule_start = models.DateField(null=True)
    occurrence = models.PositiveSmallIntegerField(default=1)
    frequency = models.CharField(choices=FREQUENCY_CHOICES, default=MONTH, max_length=5)

    def get_frequency_display(self):
        next_report = self.current_due_report()

        if self.frequency == self.MONTH:
            if self.schedule_start and self.schedule_start.day == 31:
                day_of_month = 'last day'
            else:
                day_of_month = ordinal(next_report.end_date.day)
            if self.occurrence == 1:
                return f"Monthly on the { day_of_month } of the month"
            return f"Every { self.occurrence } months on the { day_of_month } of the month"

        weekday = next_report.end_date.strftime('%A')

        if self.occurrence == 1:
            return f"Every week on { weekday }"
        return f"Every {self.occurrence} weeks on { weekday }"

    def is_up_to_date(self):
        return len(self.project.reports.to_do()) == 0

    def outstanding_reports(self):
        return len(self.project.reports.to_do())

    def has_very_late_reports(self):
        return self.project.reports.any_very_late()

    def past_due_reports(self):
        return self.project.reports.to_do()

    def last_report(self):
        today = timezone.now().date()
        # Get the most recent report that was either:
        # - due by today and not submitted
        # - was skipped but due after today
        # - was submitted but due after today
        return self.project.reports.filter(
            Q(end_date__lt=today) |
            Q(skipped=True) |
            Q(submitted__isnull=False)
        ).first()

    def current_due_report(self):
        # Project not started - no reporting required
        if not self.project.start_date:
            return None

        today = timezone.now().date()

        last_report = self.last_report()

        schedule_date = self.schedule_start or self.project.start_date

        if last_report:
            if last_report.end_date < schedule_date:
                # reporting schedule changed schedule_start is now the next report date
                next_due_date = schedule_date
            else:
                # we've had a report since the schedule date so base next deadline from the report
                next_due_date = self.next_date(last_report.end_date)
        else:
            # first report required
            if self.schedule_start and self.schedule_start >= today:
                # Schedule changed since project inception
                next_due_date = self.schedule_start
            else:
                # schedule_start is the first day the project so the "last" period
                # ended one day before that. If date is in past we required report now
                next_due_date = max(
                    self.next_date(schedule_date - relativedelta(days=1)),
                    today,
                )

        report, _ = self.project.reports.update_or_create(
            project=self.project,
            current__isnull=True,
            skipped=False,
            end_date__gte=today,
            defaults={'end_date': next_due_date}
        )
        return report

    def next_date(self, last_date):
        delta_frequency = self.frequency + 's'
        delta = relativedelta(**{delta_frequency: self.occurrence})
        next_date = last_date + delta
        return next_date


class ReportQueryset(models.QuerySet):
    def done(self):
        return self.filter(
            Q(current__isnull=False) | Q(skipped=True),
        )

    def to_do(self):
        today = timezone.now().date()
        return self.filter(
            current__isnull=True,
            skipped=False,
            end_date__lt=today,
        ).order_by('end_date')

    def any_very_late(self):
        two_weeks_ago = timezone.now().date() - relativedelta(weeks=2)
        return self.to_do().filter(end_date__lte=two_weeks_ago)

    def submitted(self):
        return self.filter(current__isnull=False)

    def for_table(self):
        return self.annotate(
            last_end_date=Subquery(
                Report.objects.filter(
                    project=OuterRef('project_id'),
                    end_date__lt=OuterRef('end_date')
                ).values('end_date')[:1]
            ),
            project_start_date=Subquery(
                Project.objects.filter(
                    pk=OuterRef('project_id'),
                ).with_start_date().values('start')[:1]
            ),
            start=Case(
                When(
                    last_end_date__isnull=False,
                    # Expression Wrapper doesn't cast the calculated object
                    # Use cast to get an actual date object
                    then=Cast(
                        ExpressionWrapper(
                            F('last_end_date') + datetime.timedelta(days=1),
                            output_field=models.DateTimeField(),
                        ),
                        models.DateField(),
                    ),
                ),
                default=F('project_start_date'),
                output_field=models.DateField(),
            )
        )


class Report(models.Model):
    skipped = models.BooleanField(default=False)
    end_date = models.DateField()
    project = models.ForeignKey("Project", on_delete=models.CASCADE, related_name="reports")
    submitted = models.DateTimeField(null=True)
    notified = models.DateTimeField(null=True)
    current = models.OneToOneField(
        "ReportVersion",
        on_delete=models.CASCADE,
        related_name='live_for_report',
        null=True,
    )
    draft = models.OneToOneField(
        "ReportVersion",
        on_delete=models.CASCADE,
        related_name='draft_for_report',
        null=True,
    )

    objects = ReportQueryset.as_manager()

    class Meta:
        ordering = ('-end_date',)

    def get_absolute_url(self):
        return reverse('apply:projects:reports:detail', kwargs={'pk': self.pk})

    @property
    def previous(self):
        return Report.objects.submitted().filter(
            project=self.project_id,
            end_date__lt=self.end_date,
        ).exclude(
            pk=self.pk,
        ).first()

    @property
    def next(self):
        return Report.objects.submitted().filter(
            project=self.project_id,
            end_date__gt=self.end_date,
        ).exclude(
            pk=self.pk,
        ).order_by('end_date').first()

    @property
    def past_due(self):
        return timezone.now().date() > self.end_date

    @property
    def is_very_late(self):
        two_weeks_ago = timezone.now().date() - relativedelta(weeks=2)
        two_weeks_late = self.end_date < two_weeks_ago
        not_submitted = not self.current
        return not_submitted and two_weeks_late

    @property
    def can_submit(self):
        return self.start_date <= timezone.now().date() and not self.skipped

    @property
    def submitted_date(self):
        if self.submitted:
            return self.submitted.date()

    @cached_property
    def start_date(self):
        last_report = self.project.reports.filter(end_date__lt=self.end_date).first()
        if last_report:
            return last_report.end_date + relativedelta(days=1)

        return self.project.start_date


class ReportVersion(models.Model):
    report = models.ForeignKey("Report", on_delete=models.CASCADE, related_name="versions")
    submitted = models.DateTimeField()
    public_content = models.TextField()
    private_content = models.TextField()
    draft = models.BooleanField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reports",
        null=True,
    )


class ReportPrivateFiles(models.Model):
    report = models.ForeignKey("ReportVersion", on_delete=models.CASCADE, related_name="files")
    document = models.FileField(upload_to=report_path, storage=PrivateStorage())

    @property
    def filename(self):
        return os.path.basename(self.document.name)

    def __str__(self):
        return self.filename

    def get_absolute_url(self):
        return reverse('apply:projects:reports:document', kwargs={'pk': self.report.report_id, 'file_pk': self.pk})
