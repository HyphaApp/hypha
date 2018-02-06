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
from wagtail.wagtailcore.models import Orderable, Page
from wagtail.wagtailforms.models import AbstractEmailForm, AbstractFormSubmission

from opentech.apply.stream_forms.models import AbstractStreamForm

from .blocks import CustomFormFieldsBlock, MustIncludeFieldBlock, REQUIRED_BLOCK_NAMES
from .forms import WorkflowFormAdminForm
from .workflow import SingleStage, DoubleStage


WORKFLOW_CLASS = {
    SingleStage.name: SingleStage,
    DoubleStage.name: DoubleStage,
}


def admin_url(page):
    return reverse('wagtailadmin_pages:edit', args=(page.id,))


class SubmittableStreamForm(AbstractStreamForm):
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
            User = get_user_model()
            email = cleaned_data.get('email')
            full_name = cleaned_data.get('full_name')
            user, _ = User.objects.get_or_create_and_notify(
                email=email,
                defaults={'full_name': full_name}
            )

        return self.get_submission_class().objects.create(
            form_data=cleaned_data,
            **self.get_submit_meta_data(user=user),
        )

    def get_submit_meta_data(self, **kwargs):
        return kwargs


class DefinableWorkflowStreamForm(AbstractEmailForm, AbstractStreamForm):
    class Meta:
        abstract = True

    base_form_class = WorkflowFormAdminForm

    WORKFLOWS = {
        'single': SingleStage.name,
        'double': DoubleStage.name,
    }

    workflow = models.CharField(choices=WORKFLOWS.items(), max_length=100, default='single')
    confirmation_text_extra = models.TextField(blank=True, help_text="Additional text for the application confirmation message.")

    def get_defined_fields(self):
        # Only return the first form, will need updating for when working with 2 stage WF
        return self.forms.all()[0].fields

    @property
    def workflow_class(self):
        return WORKFLOW_CLASS[self.get_workflow_display()]

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

        subject = self.subject if self.subject else 'Thank You for Your submission to Open Technology Fund'
        send_mail(subject, render_to_string('funds/email/confirmation.txt', context), (email,), self.from_address, )

    content_panels = AbstractStreamForm.content_panels + [
        FieldPanel('workflow'),
        InlinePanel('forms', label="Forms"),
    ]

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

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading='Content'),
        ObjectList(email_confirmation_panels, heading='Confirmation email'),
        ObjectList(Page.promote_panels, heading='Promote'),
        ObjectList(Page.settings_panels, heading='Settings', classname="settings"),
    ])


class FundType(DefinableWorkflowStreamForm):
    class Meta:
        verbose_name = _("Fund")

    parent_page_types = ['apply_home.ApplyHomePage']
    subpage_types = ['funds.Round']

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


class FundForm(Orderable):
    form = models.ForeignKey('ApplicationForm')
    fund = ParentalKey('FundType', related_name='forms')

    @property
    def fields(self):
        return self.form.form_fields


class ApplicationForm(models.Model):
    name = models.CharField(max_length=255)
    form_fields = StreamField(CustomFormFieldsBlock())

    panels = [
        FieldPanel('name'),
        StreamFieldPanel('form_fields'),
    ]

    def __str__(self):
        return self.name


class Round(SubmittableStreamForm):
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
        ], heading="Dates")
    ]

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

    def get_defined_fields(self):
        # Only return the first form, will need updating for when working with 2 stage WF
        return self.get_parent().specific.forms.all()[0].fields

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


class LabType(DefinableWorkflowStreamForm, SubmittableStreamForm):  # type: ignore
    class Meta:
        verbose_name = _("Lab")

    parent_page_types = ['apply_home.ApplyHomePage']
    subpage_types = []  # type: ignore

    def get_defined_fields(self):
        # Only return the first form, will need updating for when working with 2 stage WF
        return self.specific.forms.all()[0].fields

    def get_submit_meta_data(self, **kwargs):
        return super().get_submit_meta_data(
            page=self,
            round=None,
            **kwargs,
        )

    def open_round(self):
        return self.live


class LabForm(Orderable):
    form = models.ForeignKey('ApplicationForm')
    lab = ParentalKey('LabType', related_name='forms')

    @property
    def fields(self):
        return self.form.form_fields


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


class ApplicationSubmission(AbstractFormSubmission):
    form_data = JSONField(encoder=DjangoJSONEncoder)
    round = models.ForeignKey('wagtailcore.Page', on_delete=models.CASCADE, related_name='submissions', null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    objects = JSONOrderable.as_manager()

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
        return super().__getattr__(item)

    def __str__(self):
        return str(super().__str__())
