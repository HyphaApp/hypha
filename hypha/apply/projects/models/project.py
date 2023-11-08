import decimal
import json
import logging

from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Count, F, Max, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Cast, Coalesce
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import StreamField
from wagtail.models import Orderable

from hypha.addressfield.fields import ADDRESS_FIELDS_ORDER
from hypha.apply.funds.models.mixins import AccessFormData
from hypha.apply.stream_forms.files import StreamFieldDataEncoder
from hypha.apply.stream_forms.models import BaseStreamForm
from hypha.apply.utils.storage import PrivateStorage

from ..blocks import ProjectFormCustomFormFieldsBlock
from .vendor import Vendor

logger = logging.getLogger(__name__)


def contract_path(instance, filename):
    return f"projects/{instance.project_id}/contracts/{filename}"


def document_path(instance, filename):
    return f"projects/{instance.project_id}/supporting_documents/{filename}"


def document_template_path(instance, filename):
    return f"projects/supporting_documents/{instance.id}/template/{filename}"


def contract_document_template_path(instance, filename):
    return f"projects/contract_documents/{instance.id}/template/{filename}"


def contract_document_path(instance, filename):
    return f"projects/{instance.project_id}/contracting_documents/{filename}"


PROJECT_ACTION_MESSAGE_TAG = "project_action_message"

APPROVE = "approve"
REQUEST_CHANGE = "request_change"
PAF_STATUS_CHOICES = (
    (APPROVE, "Approve"),
    (REQUEST_CHANGE, "Request changes or more information"),
)

DRAFT = "draft"
INTERNAL_APPROVAL = "internal_approval"
CONTRACTING = "contracting"
INVOICING_AND_REPORTING = "invoicing_and_reporting"
CLOSING = "closing"
COMPLETE = "complete"
PROJECT_STATUS_CHOICES = [
    (DRAFT, _("Draft")),
    (INTERNAL_APPROVAL, _("Internal approval")),
    (CONTRACTING, _("Contracting")),
    (INVOICING_AND_REPORTING, _("Invoicing and reporting")),
    (CLOSING, _("Closing")),
    (COMPLETE, _("Complete")),
]
PROJECT_PUBLIC_STATUSES = [
    (DRAFT, _("Draft")),
    (INTERNAL_APPROVAL, _("{} approval").format(settings.ORG_SHORT_NAME)),
    (CONTRACTING, _("Contracting")),
    (INVOICING_AND_REPORTING, _("Invoicing and reporting")),
    (CLOSING, _("Closing")),
    (COMPLETE, _("Complete")),
]


class ProjectQuerySet(models.QuerySet):
    def active(self):
        # Projects that are not finished.
        return self.exclude(status=COMPLETE)

    def in_progress(self):
        # Projects that users need to interact with, submitting reports or payment request.
        return self.filter(
            status__in=(
                INVOICING_AND_REPORTING,
                CLOSING,
            )
        )

    def complete(self):
        return self.filter(status=COMPLETE)

    def in_contracting(self):
        return self.filter(status=CONTRACTING)

    def internal_approval(self):
        return self.filter(
            status=INTERNAL_APPROVAL,
        )

    def by_end_date(self, desc=False):
        order = getattr(F("proposed_end"), "desc" if desc else "asc")(nulls_last=True)

        return self.order_by(order)

    def with_amount_paid(self):
        return self.annotate(
            amount_paid=Coalesce(
                Sum("invoices__paid_value"),
                Value(0),
                output_field=models.DecimalField(),
            ),
        )

    def with_last_payment(self):
        return self.annotate(
            last_payment_request=Max(
                "invoices__requested_at", output_field=models.DateTimeField()
            ),
        )

    def with_outstanding_reports(self):
        Report = apps.get_model("application_projects", "Report")
        return self.annotate(
            outstanding_reports=Subquery(
                Report.objects.filter(
                    project=OuterRef("pk"),
                )
                .to_do()
                .order_by()
                .values("project")
                .annotate(
                    count=Count("pk"),
                )
                .values("count"),
                output_field=models.IntegerField(),
            )
        )

    def with_start_date(self):
        return self.annotate(
            start=Cast(
                Subquery(
                    Contract.objects.filter(
                        project=OuterRef("pk"),
                    )
                    .approved()
                    .order_by("approved_at")
                    .values("approved_at")[:1]
                ),
                models.DateField(),
            )
        )

    def for_table(self):
        return (
            self.with_amount_paid()
            .with_last_payment()
            .with_outstanding_reports()
            .select_related(
                "report_config",
                "submission__page",
                "lead",
            )
        )


class Project(BaseStreamForm, AccessFormData, models.Model):
    lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="lead_projects",
    )
    submission = models.OneToOneField(
        "funds.ApplicationSubmission", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="owned_projects",
    )

    title = models.TextField()
    vendor = models.ForeignKey(
        "application_projects.Vendor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
    )
    value = models.DecimalField(
        default=0,
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(limit_value=0)],
    )
    proposed_start = models.DateTimeField(_("Proposed Start Date"), null=True)
    proposed_end = models.DateTimeField(_("Proposed End Date"), null=True)

    status = models.TextField(choices=PROJECT_STATUS_CHOICES, default=DRAFT)

    form_data = models.JSONField(encoder=StreamFieldDataEncoder, default=dict)
    form_fields = StreamField(
        ProjectFormCustomFormFieldsBlock(), null=True, use_json_field=True
    )

    # tracks read/write state of the Project
    is_locked = models.BooleanField(default=False)

    # tracks updates to the Projects fields via the Project Application Form.
    user_has_updated_details = models.BooleanField(default=False)
    submitted_contract_documents = models.BooleanField(
        "Submit Contracting Documents", default=False
    )

    activities = GenericRelation(
        "activity.Activity",
        content_type_field="source_content_type",
        object_id_field="source_object_id",
        related_query_name="project",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    external_projectid = models.CharField(
        max_length=30,
        blank=True,
        help_text="ID of this project at integrated payment service.",
    )
    external_project_information = models.JSONField(
        default=dict,
        help_text="More details of the project integrated at payment service.",
    )
    sent_to_compliance_at = models.DateTimeField(null=True)

    paf_reviews_meta_data = models.JSONField(
        default=dict, help_text="Reviewers role and their actions/comments"
    )

    objects = ProjectQuerySet.as_manager()

    wagtail_reference_index_ignore = True

    def __str__(self):
        return self.title

    @property
    def status_display(self):
        return self.get_status_display()

    def get_address_display(self):
        try:
            address = json.loads(self.vendor.address)
        except (json.JSONDecodeError, AttributeError):
            return ""
        else:
            return ", ".join(
                address.get(field)
                for field in ADDRESS_FIELDS_ORDER
                if address.get(field)
            )

    @classmethod
    def create_from_submission(cls, submission, lead=None):
        """
        Create a Project from the given submission.

        Returns a new Project or the given ApplicationSubmissions existing
        Project.
        """
        if not settings.PROJECTS_ENABLED:
            logging.error(
                f"Tried to create a Project for Submission ID={submission.id} while projects are disabled"
            )
            return None

        # OneToOne relations on the targetted model cannot be accessed without
        # an exception when the relation doesn't exist (is None).  Since we
        # want to fail fast here, we can use hasattr instead.
        if hasattr(submission, "project"):
            return submission.project

        # See if there is a form field named "legal name", if not use user name.
        legal_name = (
            submission.get_answer_from_label("legal name") or submission.user.full_name
        )
        vendor, _ = Vendor.objects.get_or_create(user=submission.user)
        vendor.name = legal_name
        vendor.address = submission.form_data.get("address", "")
        vendor.save()
        return Project.objects.create(
            submission=submission,
            user=submission.user,
            title=submission.title,
            vendor=vendor,
            lead=lead if lead else None,
            value=submission.form_data.get("value", 0),
        )

    @property
    def start_date(self):
        # Assume project starts when OTF are happy with the first signed contract
        first_approved_contract = (
            self.contracts.approved().order_by("approved_at").first()
        )
        if not first_approved_contract:
            return None
        return first_approved_contract.approved_at.date()

    @property
    def end_date(self):
        # Aiming for the proposed end date as the last day of the project
        # If still ongoing assume today is the end
        if self.proposed_end:
            return max(
                self.proposed_end.date(),
                timezone.now().date(),
            )
        return timezone.now().date()

    def paid_value(self):
        return self.invoices.paid_value()

    def unpaid_value(self):
        return self.invoices.unpaid_value()

    def clean(self):
        if self.proposed_start is None:
            return

        if self.proposed_end is None:
            return

        if self.proposed_start > self.proposed_end:
            raise ValidationError(
                _("Proposed End Date must be after Proposed Start Date")
            )

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
            # Approver can edit it when they are approving
            if self.can_make_approval:
                if user.is_finance or user.is_approver or user.is_contracting:
                    return True

            # Lead can make changes to the project
            if user == self.lead:
                return True

            # Staff can edit project
            if user.is_apply_staff:
                return True
        return False

    @property
    def editable(self):
        if self.is_locked:
            return False
        elif (
            self.status == DRAFT
        ):  # locked condition is enough,it is just for double check
            return True
        return False

    def get_absolute_url(self):
        return reverse("apply:projects:detail", args=[self.id])

    @property
    def can_make_approval(self):
        return self.status == INTERNAL_APPROVAL

    @property
    def is_approved_by_all_paf_reviewers(self):
        if self.status == INTERNAL_APPROVAL:
            if not self.paf_approvals.filter(approved=False):
                return True
        return False

    @property
    def can_update_paf_status(self):
        return self.status == INTERNAL_APPROVAL

    def can_request_funding(self):
        """
        Should we show this Project's funding block?
        """
        return self.status in (CLOSING, INVOICING_AND_REPORTING)

    @property
    def can_send_for_approval(self):
        """
        Wrapper to expose the pending approval state

        We don't want to expose a "Sent for Approval" state to the end User so
        we infer it from the current status being "Comitted" and the Project
        being locked.
        """
        correct_state = self.status == DRAFT and not self.is_locked
        return correct_state and self.user_has_updated_details

    @property
    def is_in_progress(self):
        return self.status == INVOICING_AND_REPORTING

    @property
    def has_deliverables(self):
        return self.deliverables.exists()

    @property
    def program_project_id(self):
        """
        Program project id is used to fetch deliverables from IntAcct.

        Stored in external_project_information as the first item of referenceno(PONUMBER).
        """
        reference_number = self.external_project_information.get("PONUMBER", None)
        if reference_number:
            return reference_number.split("-")[0]
        return ""


class ProjectSOW(BaseStreamForm, AccessFormData, models.Model):
    project = models.OneToOneField(
        Project, related_name="sow", on_delete=models.CASCADE
    )
    form_data = models.JSONField(encoder=StreamFieldDataEncoder, default=dict)
    form_fields = StreamField(
        ProjectFormCustomFormFieldsBlock(), null=True, use_json_field=True
    )


class ProjectBaseStreamForm(BaseStreamForm, models.Model):
    name = models.CharField(max_length=255)
    form_fields = StreamField(ProjectFormCustomFormFieldsBlock(), use_json_field=True)

    panels = [
        FieldPanel("name"),
        FieldPanel("form_fields"),
    ]

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class ProjectForm(ProjectBaseStreamForm):
    class Meta:
        db_table = "project_form"


class ProjectSOWForm(ProjectBaseStreamForm):
    class Meta:
        db_table = "project_sow_form"


class ProjectReportForm(ProjectBaseStreamForm):
    """
    An Applicant Report Form can be attached to a Fund to collect reports from Applicants aka Grantees during the
    Project. It is only relevant for accepted or granted Submissions which is why it is attached to Project. It is
    similar to the other Forms (PAF, SOW) in that it uses StreamForm to allow maximum flexibility in form creation.
    See Also ReportVersion where the fields from the form get copied and the response data gets filled in.
    """

    pass


class PAFReviewersRole(Orderable, ClusterableModel):
    label = models.CharField(max_length=200)
    user_roles = ParentalManyToManyField(
        Group,
        verbose_name=_("user groups"),
        help_text=_(
            "Only selected group's users will be listed for this PAFReviewerRole"
        ),
        related_name="paf_reviewers_roles",
    )
    page = ParentalKey("ProjectSettings", related_name="paf_reviewers_roles")

    panels = [
        FieldPanel("label"),
        FieldPanel("user_roles", widget=forms.CheckboxSelectMultiple),
    ]

    def __str__(self):
        return str(self.label)


class ProjectReminderFrequency(Orderable, ClusterableModel):
    num_days = models.IntegerField()
    page = ParentalKey("ProjectSettings", related_name="reminder_frequencies")

    class FrequencyRelation(models.TextChoices):
        BEFORE = "BE", _("Before")
        AFTER = "AF", _("After")

    relation = models.CharField(
        max_length=2,
        choices=FrequencyRelation.choices,
        default=FrequencyRelation.BEFORE,
    )

    panels = [
        FieldPanel("num_days", heading=_("Number of Days")),
        FieldPanel("relation", heading=_("Relation to Project Due Date")),
    ]


@register_setting
class ProjectSettings(BaseSiteSetting, ClusterableModel):
    contracting_gp_email = models.TextField(
        "Contracting Group Email", null=True, blank=True
    )
    finance_gp_email = models.TextField("Finance Group Email", null=True, blank=True)
    staff_gp_email = models.TextField("Staff Group Email", null=True, blank=True)
    vendor_setup_required = models.BooleanField(default=True)
    paf_approval_sequential = models.BooleanField(
        default=True, help_text="Uncheck it to approve project parallely"
    )

    panels = [
        FieldPanel("staff_gp_email"),
        FieldPanel("contracting_gp_email"),
        FieldPanel("finance_gp_email"),
        FieldPanel("vendor_setup_required"),
        MultiFieldPanel(
            [
                FieldPanel(
                    "paf_approval_sequential", heading="Approve Project Sequentially"
                ),
                InlinePanel("paf_reviewers_roles", label=_("Project Reviewers Roles")),
            ],
            heading=_("Project Reviewers Roles"),
            help_text=_(
                "Reviewer Roles are needed to move projects to 'Internal Approval' stage. "
                "Delete all roles to skip internal approval process and "
                "to move all internal approval projects back to the 'Draft' stage with all approvals removed."
            ),
        ),
        InlinePanel(
            "reminder_frequencies",
            label=_("Report Reminder Frequency"),
            heading=_("Report Reminder Frequency"),
        ),
    ]


class PAFApprovals(models.Model):
    project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="paf_approvals"
    )
    paf_reviewer_role = models.ForeignKey(
        "PAFReviewersRole", on_delete=models.CASCADE, related_name="paf_approvals"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="paf_approvals",
    )
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField()
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ["project", "paf_reviewer_role"]
        ordering = ["paf_reviewer_role__sort_order"]

    def __str__(self):
        return _("Approval of {project} by {user}").format(
            project=self.project, user=self.user
        )

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        return super().save(*args, **kwargs)


class ContractQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(
            Q(signed_by_applicant=True) | Q(signed_and_approved=True)
        ).filter(approver__isnull=False)


class Contract(models.Model):
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="contracts",
    )
    project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="contracts"
    )

    file = models.FileField(upload_to=contract_path, storage=PrivateStorage())

    signed_and_approved = models.BooleanField("Signed and approved", default=False)

    signed_by_applicant = models.BooleanField("Counter Signed?", default=False)
    uploaded_by_contractor_at = models.DateTimeField(null=True)
    uploaded_by_applicant_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(null=True)

    objects = ContractQuerySet.as_manager()

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        return super().save(*args, **kwargs)

    @property
    def state(self):
        return _("Counter Signed") if self.signed_by_applicant else _("Unsigned")

    def __str__(self):
        return _("Contract for {project} ({state})").format(
            project=self.project, state=self.state
        )

    def get_absolute_url(self):
        return reverse("apply:projects:contract", args=[self.project.pk, self.pk])


class PacketFile(models.Model):
    category = models.ForeignKey(
        "DocumentCategory",
        null=True,
        on_delete=models.CASCADE,
        related_name="packet_files",
    )
    project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="packet_files"
    )

    title = models.TextField()
    document = models.FileField(upload_to=document_path, storage=PrivateStorage())
    created_at = models.DateField(auto_now_add=True, null=True)

    def __str__(self):
        return _("Project file: {title}").format(title=self.title)

    class Meta:
        ordering = ("-created_at",)

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


class ContractPacketFile(models.Model):
    category = models.ForeignKey(
        "ContractDocumentCategory",
        null=True,
        on_delete=models.CASCADE,
        related_name="contract_packet_files",
    )
    project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="contract_packet_files"
    )

    title = models.TextField()
    document = models.FileField(
        upload_to=contract_document_path, storage=PrivateStorage()
    )
    created_at = models.DateField(auto_now_add=True, null=True)

    def __str__(self):
        return _("Contract file: {title}").format(title=self.title)

    def get_remove_form(self):
        """
        Get an instantiated RemoveContractDocumentForm with this class as `instance`.

        This allows us to build instances of the RemoveContractDocumentForm for each
        instance of ContractPacketFile in the contracting documents template.  The
        standard Delegated View flow makes it difficult to create these forms
        in the view or template.
        """
        from ..forms import RemoveContractDocumentForm

        return RemoveContractDocumentForm(instance=self)


@receiver(post_delete, sender=ContractPacketFile)
def delete_contractpacketfile_file(sender, instance, **kwargs):
    # Remove the file and don't save the base model
    instance.document.delete(False)


class DocumentCategory(models.Model):
    name = models.CharField(max_length=254)
    recommended_minimum = models.PositiveIntegerField(null=True, blank=True)
    required = models.BooleanField(default=False)
    template = models.FileField(
        upload_to=document_template_path,
        storage=PrivateStorage(),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("-required", "name")
        verbose_name_plural = "Project Document Categories"

    panels = [
        FieldPanel("name"),
        FieldPanel("required"),
        FieldPanel("template"),
    ]


class ContractDocumentCategory(models.Model):
    name = models.CharField(max_length=254)
    recommended_minimum = models.PositiveIntegerField(null=True, blank=True)
    required = models.BooleanField(default=True)
    template = models.FileField(
        upload_to=contract_document_template_path,
        storage=PrivateStorage(),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("-required", "name")
        verbose_name_plural = "Contract Document Categories"

    panels = [
        FieldPanel("name"),
        FieldPanel("required"),
        FieldPanel("template"),
    ]


class Deliverable(models.Model):
    external_id = models.CharField(
        max_length=30,
        blank=True,
        help_text="ID of this deliverable at integrated payment service.",
    )
    name = models.TextField()
    available_to_invoice = models.IntegerField(default=1)
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(decimal.Decimal("0.01"))],
    )
    extra_information = models.JSONField(
        default=dict,
        help_text="More details of the deliverable at integrated payment service.",
    )
    project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="deliverables",
    )

    def __str__(self):
        return self.name
