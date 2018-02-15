from datetime import date

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Q
from django.db.models.expressions import RawSQL, OrderBy
from django.http import Http404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.text import mark_safe
from django.utils.translation import ugettext_lazy as _

from modelcluster.fields import ParentalKey
from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel,
    FieldRowPanel,
    InlinePanel,
    MultiFieldPanel,
    ObjectList,
    StreamFieldPanel,
    TabbedInterface
)

from wagtail.wagtailadmin.utils import send_mail
from wagtail.wagtailcore.fields import StreamField
from wagtail.wagtailcore.models import Orderable
from wagtail.wagtailforms.models import AbstractEmailForm, AbstractFormSubmission

from opentech.apply.stream_forms.models import AbstractStreamForm

from .blocks import CustomFormFieldsBlock, MustIncludeFieldBlock, REQUIRED_BLOCK_NAMES
from .edit_handlers import FilteredFieldPanel, ReadOnlyPanel, ReadOnlyInlinePanel
from .forms import WorkflowFormAdminForm
from .workflow import SingleStage, DoubleStage


WORKFLOW_CLASS = {
    SingleStage.name: SingleStage,
    DoubleStage.name: DoubleStage,
}


def admin_url(page):
    return reverse('wagtailadmin_pages:edit', args=(page.id,))


class SubmittableStreamForm(AbstractStreamForm):
    """
    Controls how stream forms are submitted. Any Page allowing submissions should inherit from here.
    """
    class Meta:
        abstract = True

    def get_submission_class(self):
        return ApplicationSubmission

    def process_form_submission(self, form):
        cleaned_data = form.cleaned_data
        for field in self.get_defined_fields():
            # Update the ids which are unique to use the unique name
            if isinstance(field.block, MustIncludeFieldBlock):
                response = cleaned_data.pop(field.id)
                cleaned_data[field.block.name] = response

        if form.user.is_authenticated():
            user = form.user
            cleaned_data['email'] = user.email
            cleaned_data['full_name'] = user.get_full_name()
        else:
            # Rely on the form having the following must include fields (see blocks.py)
            email = cleaned_data.get('email')
            full_name = cleaned_data.get('full_name')

            User = get_user_model()
            user, _ = User.objects.get_or_create_and_notify(
                email=email,
                site=self.get_site(),
                defaults={'full_name': full_name}
            )

        return self.get_submission_class().objects.create(
            form_data=cleaned_data,
            form_fields=self.get_defined_fields(),
            **self.get_submit_meta_data(user=user),
        )

    def get_submit_meta_data(self, **kwargs):
        return kwargs


class WorkflowHelpers(models.Model):
    """
    Defines the common methods and fields for working with Workflows within Django models
    """
    class Meta:
        abstract = True

    WORKFLOWS = {
        'single': SingleStage.name,
        'double': DoubleStage.name,
    }

    workflow_name = models.CharField(choices=WORKFLOWS.items(), max_length=100, default='single', verbose_name="Workflow")

    @property
    def workflow(self):
        # Pretend we have forms associated with the workflow.
        # TODDO Confirm if we need forms on the workflow.
        return self.workflow_class([None] * len(self.workflow_class.stage_classes))

    @property
    def workflow_class(self):
        return WORKFLOW_CLASS[self.get_workflow_name_display()]

    @classmethod
    def workflow_class_from_name(cls, name):
        return WORKFLOW_CLASS[cls.WORKFLOWS[name]]


class WorkflowStreamForm(WorkflowHelpers, AbstractStreamForm):  # type: ignore
    """
    Defines the common methods and fields for working with Workflows within Wagtail pages
    """
    class Meta:
        abstract = True

    def get_defined_fields(self):
        # Only return the first form, will need updating for when working with 2 stage WF
        return self.forms.all()[0].fields

    content_panels = AbstractStreamForm.content_panels + [
        FieldPanel('workflow_name'),
        InlinePanel('forms', label="Forms"),
    ]


class EmailForm(AbstractEmailForm):
    """
    Defines the behaviour for pages that hold information about emailing applicants

    Email Confirmation Panel should be included to allow admins to make changes.
    """
    class Meta:
        abstract = True

    confirmation_text_extra = models.TextField(blank=True, help_text="Additional text for the application confirmation message.")

    def process_form_submission(self, form):
        submission = super().process_form_submission(form)
        self.send_mail(form)
        return submission

    def send_mail(self, form):
        data = form.cleaned_data
        email = data.get('email')
        context = {
            'name': data.get('full_name'),
            'email': email,
            'project_name': data.get('title'),
            'extra_text': self.confirmation_text_extra,
            'fund_type': self.title,
        }

        subject = self.subject if self.subject else 'Thank you for your submission to Open Technology Fund'
        send_mail(subject, render_to_string('funds/email/confirmation.txt', context), (email,), self.from_address, )

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
            heading="Confirmation email",
        )
    ]

    email_tab = ObjectList(email_confirmation_panels, heading='Confirmation email')


class FundType(EmailForm, WorkflowStreamForm):  # type: ignore
    class Meta:
        verbose_name = _("Fund")

    # Adds validation around forms & workflows. Isn't on Workflow class due to not displaying workflow field on Round
    base_form_class = WorkflowFormAdminForm

    parent_page_types = ['apply_home.ApplyHomePage']
    subpage_types = ['funds.Round']

    def detail(self):
        # The location to find out more information
        return self.fund_public.first()

    @property
    def open_round(self):
        rounds = Round.objects.child_of(self).live().public().specific()
        return rounds.filter(
            Q(start_date__lte=date.today()) &
            Q(Q(end_date__isnull=True) | Q(end_date__gte=date.today()))
        ).first()

    def next_deadline(self):
        return self.open_round.end_date

    def serve(self, request):
        if hasattr(request, 'is_preview') or not self.open_round:
            return super().serve(request)

        # delegate to the open_round to use the latest form instances
        request.show_round = True
        return self.open_round.serve(request)

    edit_handler = TabbedInterface([
        ObjectList(WorkflowStreamForm.content_panels, heading='Content'),
        EmailForm.email_tab,
        ObjectList(WorkflowStreamForm.promote_panels, heading='Promote'),
    ])


class AbstractRelatedForm(Orderable):
    form = models.ForeignKey('ApplicationForm')

    panels = [
        FilteredFieldPanel('form', filter_query={'roundform__isnull': True})
    ]

    @property
    def fields(self):
        return self.form.form_fields

    class Meta(Orderable.Meta):
        abstract = True

    def __eq__(self, other):
        try:
            return self.fields == other.fields
        except AttributeError:
            return False

    def __str__(self):
        return self.form.name


class FundForm(AbstractRelatedForm):
    fund = ParentalKey('FundType', related_name='forms')


class RoundForm(AbstractRelatedForm):
    round = ParentalKey('Round', related_name='forms')


class ApplicationForm(models.Model):
    name = models.CharField(max_length=255)
    form_fields = StreamField(CustomFormFieldsBlock())

    panels = [
        FieldPanel('name'),
        StreamFieldPanel('form_fields'),
    ]

    def __str__(self):
        return self.name


class Round(WorkflowStreamForm, SubmittableStreamForm):  # type: ignore
    parent_page_types = ['funds.FundType']
    subpage_types = []  # type: ignore

    start_date = models.DateField(default=date.today)
    end_date = models.DateField(
        blank=True,
        null=True,
        default=date.today,
        help_text='When no end date is provided the round will remain open indefinitely.'
    )

    content_panels = SubmittableStreamForm.content_panels + [
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('start_date'),
                FieldPanel('end_date'),
            ]),
        ], heading="Dates"),
        ReadOnlyPanel('get_workflow_name_display', heading="Workflow"),
        ReadOnlyInlinePanel('forms', help_text="Are copied from the parent fund."),
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading='Content'),
        ObjectList(SubmittableStreamForm.promote_panels, heading='Promote'),
    ])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We attached the parent page as part of the before_create_hook
        if hasattr(self, 'parent_page'):
            self.workflow_name = self.parent_page.workflow_name

    def save(self, *args, **kwargs):
        is_new = not self.id
        if is_new and hasattr(self, 'parent_page'):
            # Ensure that the workflow hasn't changed
            self.workflow_name = self.parent_page.workflow_name

        super().save(*args, **kwargs)

        if is_new and hasattr(self, 'parent_page'):
            # Would be nice to do this using model clusters as part of the __init__
            for form in self.parent_page.forms.all():
                # Create a copy of the existing form object
                new_form = form.form
                new_form.id = None
                new_form.name = '{} for {} ({})'.format(new_form.name, self.title, self.get_parent().title)
                new_form.save()
                RoundForm.objects.create(round=self, form=new_form)

    def get_submit_meta_data(self, **kwargs):
        return super().get_submit_meta_data(
            page=self.get_parent(),
            round=self,
            **kwargs,
        )

    def process_form_submission(self, form):
        submission = super().process_form_submission(form)
        self.get_parent().specific.send_mail(form)
        return submission

    def clean(self):
        super().clean()

        if self.end_date and self.start_date > self.end_date:
            raise ValidationError({
                'end_date': 'End date must come after the start date',
            })

        if self.end_date:
            conflict_query = (
                Q(start_date__range=[self.start_date, self.end_date]) |
                Q(end_date__range=[self.start_date, self.end_date]) |
                Q(start_date__lte=self.start_date, end_date__gte=self.end_date)
            )
        else:
            conflict_query = (
                Q(start_date__lte=self.start_date, end_date__isnull=True) |
                Q(end_date__gte=self.start_date)
            )

        if hasattr(self, 'parent_page'):
            # Check if the create hook has added the parent page, we aren't an object yet.
            # Ensures we can access related objects during the clean phase instead of save.
            base_query = Round.objects.child_of(self.parent_page)
        else:
            # don't need parent page, we are an actual object now.
            base_query = Round.objects.sibling_of(self)

        conflicting_rounds = base_query.filter(
            conflict_query
        ).exclude(id=self.id)

        if conflicting_rounds.exists():
            error_message = mark_safe('Overlaps with the following rounds:<br> {}'.format(
                '<br>'.join([
                    f'<a href="{admin_url(round)}">{round.title}</a>: {round.start_date} - {round.end_date}'
                    for round in conflicting_rounds]
                )
            ))
            error = {
                'start_date': error_message,
            }
            if self.end_date:
                error['end_date'] = error_message

            raise ValidationError(error)

    def serve(self, request):
        if hasattr(request, 'is_preview') or hasattr(request, 'show_round'):
            return super().serve(request)

        # We hide the round as only the open round is used which is displayed through the
        # fund page
        raise Http404()


class LabType(EmailForm, WorkflowStreamForm, SubmittableStreamForm):  # type: ignore
    class Meta:
        verbose_name = _("Lab")

    parent_page_types = ['apply_home.ApplyHomePage']
    subpage_types = []  # type: ignore

    edit_handler = TabbedInterface([
        ObjectList(WorkflowStreamForm.content_panels, heading='Content'),
        EmailForm.email_tab,
        ObjectList(WorkflowStreamForm.promote_panels, heading='Promote'),
    ])

    def detail(self):
        # The location to find out more information
        return self.lab_public.first()

    def get_submit_meta_data(self, **kwargs):
        return super().get_submit_meta_data(
            page=self,
            round=None,
            **kwargs,
        )

    def open_round(self):
        return self.live


class LabForm(AbstractRelatedForm):
    lab = ParentalKey('LabType', related_name='forms')


class JSONOrderable(models.QuerySet):
    def order_by(self, *field_names):
        def build_json_order_by(field):
            if field.replace('-', '') not in REQUIRED_BLOCK_NAMES:
                return field

            if field[0] == '-':
                descending = True
                field = field[1:]
            else:
                descending = False
            return OrderBy(RawSQL("LOWER(form_data->>%s)", (field,)), descending=descending)

        field_ordering = [build_json_order_by(field) for field in field_names]
        return super().order_by(*field_ordering)


class ApplicationSubmission(WorkflowHelpers, AbstractFormSubmission):
    field_template = 'funds/includes/submission_field.html'

    form_data = JSONField(encoder=DjangoJSONEncoder)
    form_fields = StreamField(CustomFormFieldsBlock())
    page = models.ForeignKey('wagtailcore.Page', on_delete=models.PROTECT)
    round = models.ForeignKey('wagtailcore.Page', on_delete=models.PROTECT, related_name='submissions', null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    # Workflow inherited from WorkflowHelpers
    status = models.CharField(max_length=254)

    objects = JSONOrderable.as_manager()

    def render_answers(self):
        context = {'fields': []}
        for field in self.form_fields:
            try:
                data = self.form_data[field.id]
            except KeyError:
                pass  # It was a named field or a paragraph
            else:
                form_field = field.block.get_field(field.value)
                if hasattr(form_field, 'choices'):
                    if isinstance(data, str):
                        data = [data]
                    choices = dict(form_field.choices)
                    try:
                        data = [choices[value] for value in data]
                    except KeyError:
                        data = [choices[int(value)] for value in data]
                else:
                    data = str(data)

                context['fields'].append({
                    'field': form_field,
                    'value': data,
                })
        return render_to_string(self.field_template, context)

    @property
    def status_name(self):
        return self.phase.name

    @property
    def stage(self):
        return self.phase.stage

    @property
    def phase(self):
        return self.workflow.current(self.status)

    def save(self, *args, **kwargs):
        if not self.id:
            # We are creating the object default to first stage
            try:
                self.workflow_name = self.round.workflow_name
            except AttributeError:
                # We are a lab submission
                self.workflow_name = self.page.workflow_name
            self.status = str(self.workflow.first())

        return super().save(*args, **kwargs)

    def get_data(self):
        # Updated for JSONField
        form_data = self.form_data
        form_data.update({
            'submit_time': self.submit_time,
        })

        return form_data

    def __getattr__(self, item):
        # fall back to values defined on the data
        if item in REQUIRED_BLOCK_NAMES:
            return self.get_data()[item]
        raise AttributeError('{} has no attribute "{}"'.format(repr(self), item))

    def __str__(self):
        return str(super().__str__())
