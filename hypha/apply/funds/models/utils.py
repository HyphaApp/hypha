from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from wagtail.admin.edit_handlers import (
    FieldPanel,
    FieldRowPanel,
    InlinePanel,
    MultiFieldPanel,
    ObjectList,
)
from wagtail.contrib.forms.models import AbstractEmailForm

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.stream_forms.models import AbstractStreamForm
from hypha.apply.users.groups import (
    COMMUNITY_REVIEWER_GROUP_NAME,
    PARTNER_GROUP_NAME,
    REVIEWER_GROUP_NAME,
    STAFF_GROUP_NAME,
)

from ..workflow import DRAFT_STATE, WORKFLOWS

REVIEW_GROUPS = [
    STAFF_GROUP_NAME,
    REVIEWER_GROUP_NAME,
    COMMUNITY_REVIEWER_GROUP_NAME,
]
LIMIT_TO_STAFF = {'groups__name': STAFF_GROUP_NAME, 'is_active': True}
LIMIT_TO_REVIEWERS = {'groups__name': REVIEWER_GROUP_NAME, 'is_active': True}
LIMIT_TO_PARTNERS = {'groups__name': PARTNER_GROUP_NAME, 'is_active': True}
LIMIT_TO_COMMUNITY_REVIEWERS = {'groups__name': COMMUNITY_REVIEWER_GROUP_NAME, 'is_active': True}
LIMIT_TO_REVIEWER_GROUPS = {'groups__name__in': REVIEW_GROUPS, 'is_active': True}


def admin_url(page):
    return reverse('wagtailadmin_pages:edit', args=(page.id,))


class WorkflowHelpers(models.Model):
    """
    Defines the common methods and fields for working with Workflows within Django models
    """
    class Meta:
        abstract = True

    WORKFLOW_CHOICES = {
        name: workflow.name
        for name, workflow in WORKFLOWS.items()
    }

    workflow_name = models.CharField(choices=WORKFLOW_CHOICES.items(), max_length=100, default='single', verbose_name=_('Workflow'))

    @property
    def workflow(self):
        return WORKFLOWS[self.workflow_name]


class SubmittableStreamForm(AbstractStreamForm):
    """
    Controls how stream forms are submitted. Any Page allowing submissions should inherit from here.
    """
    class Meta:
        abstract = True

    def get_submission_class(self):
        return self.submission_class

    def process_form_submission(self, form, draft=False):
        if not form.user.is_authenticated:
            form.user = None
        if draft:
            return self.get_submission_class().objects.create(
                form_data=form.cleaned_data,
                form_fields=self.get_defined_fields(),
                **self.get_submit_meta_data(user=form.user),
                status=DRAFT_STATE,
            )
        else:
            return self.get_submission_class().objects.create(
                form_data=form.cleaned_data,
                form_fields=self.get_defined_fields(),
                **self.get_submit_meta_data(user=form.user),
            )

    def get_submit_meta_data(self, **kwargs):
        return kwargs


class WorkflowStreamForm(WorkflowHelpers, AbstractStreamForm):  # type: ignore
    """
    Defines the common methods and fields for working with Workflows within Wagtail pages
    """
    class Meta:
        abstract = True

    def get_defined_fields(self, stage=None, form_index=0):
        if not stage:
            stage_num = 1
        else:
            stage_num = self.workflow.stages.index(stage) + 1
        return self.forms.filter(stage=stage_num)[form_index].fields

    def render_landing_page(self, request, form_submission=None, *args, **kwargs):
        # We only reach this page after creation of a new submission
        # Hook in to notify about new applications
        if not form_submission.status == DRAFT_STATE:
            messenger(
                MESSAGES.NEW_SUBMISSION,
                request=request,
                user=form_submission.user,
                source=form_submission,
            )
        return super().render_landing_page(request, form_submission, *args, **kwargs)

    content_panels = AbstractStreamForm.content_panels + [
        FieldPanel('workflow_name'),
        InlinePanel('forms', label=_('Forms')),
        InlinePanel('review_forms', label=_('Internal Review Forms')),
        InlinePanel('external_review_forms', label=_('External Review Forms')),
        InlinePanel('determination_forms', label=_('Determination Forms'))
    ]


class EmailForm(AbstractEmailForm):
    """
    Defines the behaviour for pages that hold information about emailing applicants

    Email Confirmation Panel should be included to allow admins to make changes.
    """
    class Meta:
        abstract = True

    confirmation_text_extra = models.TextField(blank=True, help_text=_('Additional text for the application confirmation message.'))

    def send_mail(self, submission):
        # Make sure we don't send emails to users here. Messaging handles that
        pass

    email_confirmation_panels = [
        MultiFieldPanel(
            [
                FieldRowPanel([
                    FieldPanel('from_address', classname="col6"),
                    FieldPanel('to_address', classname="col6"),
                ]),
                FieldPanel('subject'),
                FieldPanel('confirmation_text_extra'),
            ],
            heading=_('Confirmation email'),
        )
    ]

    email_tab = ObjectList(email_confirmation_panels, heading=_('Confirmation email'))
