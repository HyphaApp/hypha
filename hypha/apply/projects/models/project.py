import collections
import decimal
import json
import logging

from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Count, F, Max, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Cast, Coalesce
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
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

from .vendor import Vendor

logger = logging.getLogger(__name__)


def contract_path(instance, filename):
    return f'projects/{instance.project_id}/contracts/{filename}'


def document_path(instance, filename):
    return f'projects/{instance.project_id}/supporting_documents/{filename}'


COMMITTED = 'committed'
CONTRACTING = 'contracting'
IN_PROGRESS = 'in_progress'
CLOSING = 'closing'
COMPLETE = 'complete'
PROJECT_STATUS_CHOICES = [
    (COMMITTED, _('Committed')),
    (CONTRACTING, _('Contracting')),
    (IN_PROGRESS, _('In Progress')),
    (CLOSING, _('Closing')),
    (COMPLETE, _('Complete')),
]


class ProjectQuerySet(models.QuerySet):
    def active(self):
        # Projects that are not finished.
        return self.exclude(status=COMPLETE)

    def in_progress(self):
        # Projects that users need to interact with, submitting reports or payment request.
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
        Report = apps.get_model('application_projects', 'Report')
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
    vendor = models.ForeignKey(
        "application_projects.Vendor",
        on_delete=models.SET_NULL,
        null=True, blank=True, related_name='projects'
    )
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
            address = json.loads(self.vendor.address)
        except (json.JSONDecodeError, AttributeError):
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

        # See if there is a form field named "legal name", if not use user name.
        legal_name = submission.get_answer_from_label('legal name') or submission.user.full_name
        vendor, _ = Vendor.objects.get_or_create(
            user=submission.user
        )
        vendor.name = legal_name
        vendor.address = submission.form_data.get('address', '')
        vendor.save()
        return Project.objects.create(
            submission=submission,
            user=submission.user,
            title=submission.title,
            vendor=vendor,
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

    @property
    def has_deliverables(self):
        return self.deliverables.exists()

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


class ProjectApprovalForm(BaseStreamForm, models.Model):
    name = models.CharField(max_length=255)
    form_fields = StreamField(FormFieldsBlock())

    panels = [
        FieldPanel('name'),
        StreamFieldPanel('form_fields'),
    ]

    def __str__(self):
        return self.name


@register_setting
class ProjectSettings(BaseSetting):
    compliance_email = models.TextField("Compliance Email")
    vendor_setup_required = models.BooleanField(default=True)


class Approval(models.Model):
    project = models.ForeignKey("Project", on_delete=models.CASCADE, related_name="approvals")
    by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="approvals")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['project', 'by']

    def __str__(self):
        return _('Approval of {project} by {user}').format(project=self.project, user=self.by)


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
        return _('Signed') if self.is_signed else _('Unsigned')

    def __str__(self):
        return _('Contract for {project} ({state})').format(project=self.project, state=self.state)

    def get_absolute_url(self):
        return reverse('apply:projects:contract', args=[self.project.pk, self.pk])


class PacketFile(models.Model):
    category = models.ForeignKey("DocumentCategory", null=True, on_delete=models.CASCADE, related_name="packet_files")
    project = models.ForeignKey("Project", on_delete=models.CASCADE, related_name="packet_files")

    title = models.TextField()
    document = models.FileField(upload_to=document_path, storage=PrivateStorage())

    def __str__(self):
        return _('Project file: {title}').format(title=self.title)

    def get_remove_form(self):
        """
        Get an instantiated RemoveDocumentForm with this class as `instance`.

        This allows us to build instances of the RemoveDocumentForm for each
        instance of PacketFile in the supporting documents template.  The
        standard Delegated View flow makes it difficult to create these forms
        in the view or template.
       """
        from ..forms import RemoveDocumentForm
        return RemoveDocumentForm(instance=self)


@receiver(post_delete, sender=PacketFile)
def delete_packetfile_file(sender, instance, **kwargs):
    # Remove the file and don't save the base model
    instance.document.delete(False)


class DocumentCategory(models.Model):
    name = models.CharField(max_length=254)
    recommended_minimum = models.PositiveIntegerField()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'Document Categories'


class Deliverable(models.Model):
    name = models.TextField()
    available_to_invoice = models.IntegerField(default=1)
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(decimal.Decimal('0.01'))],
    )
    project = models.ForeignKey(
        Project,
        null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='deliverables'
    )

    def __str__(self):
        return self.name
