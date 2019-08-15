import collections
import decimal
import json
import logging

from addressfield.fields import ADDRESS_FIELDS_ORDER
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext as _

from opentech.apply.utils.storage import PrivateStorage


logger = logging.getLogger(__name__)


class Approval(models.Model):
    project = models.ForeignKey("Project", on_delete=models.CASCADE, related_name="approvals")
    by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="approvals")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['project', 'by']

    def __str__(self):
        return f'Approval of "{self.project.title}" by {self.by}'


def document_path(instance, filename):
    return f'projects/{instance.project_id}/supporting_documents/{filename}'


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


COMMITTED = 'committed'
CONTRACTING = 'contracting'
PROJECT_STATUS_CHOICES = [
    (COMMITTED, 'Committed'),
    (CONTRACTING, 'Contracting'),
    ('in_progress', 'In Progress'),
    ('closing', 'Closing'),
    ('complete', 'Complete'),
]


class Project(models.Model):
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

    def __str__(self):
        return self.title

    def get_address_display(self):
        address = json.loads(self.contact_address)
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

    def clean(self):
        if self.proposed_start is None:
            return

        if self.proposed_end is None:
            return

        if self.proposed_start > self.proposed_end:
            raise ValidationError(_('Proposed End Date must be after Proposed Start Date'))

    def editable_by(self, user):
        if self.editable:
            return True

        # Approver can edit it when they are approving
        return user.is_approver and self.can_make_approval

    @property
    def editable(self):
        # Someone must lead the project to make changes
        return self.lead and not self.is_locked

    def get_absolute_url(self):
        if settings.PROJECTS_ENABLED:
            return reverse('apply:projects:detail', args=[self.id])
        return '#'

    @property
    def can_make_approval(self):
        return self.is_locked and self.status == COMMITTED

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


class DocumentCategory(models.Model):
    name = models.CharField(max_length=254)
    recommended_minimum = models.PositiveIntegerField()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'Document Categories'
