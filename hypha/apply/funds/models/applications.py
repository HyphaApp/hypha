from datetime import date

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import (
    Case,
    CharField,
    Count,
    F,
    FloatField,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    When,
)
from django.db.models.functions import Coalesce, Left, Length
from django.http import Http404
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalManyToManyField
from wagtail.admin.edit_handlers import (
    FieldPanel,
    FieldRowPanel,
    MultiFieldPanel,
    ObjectList,
    TabbedInterface,
)
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page, PageManager, PageQuerySet

from ..admin_forms import RoundBasePageAdminForm, WorkflowFormAdminForm
from ..edit_handlers import ReadOnlyInlinePanel, ReadOnlyPanel
from ..workflow import OPEN_CALL_PHASES
from .submissions import ApplicationSubmission
from .utils import (
    LIMIT_TO_REVIEWERS,
    LIMIT_TO_STAFF,
    EmailForm,
    SubmittableStreamForm,
    WorkflowStreamForm,
    admin_url,
)


class ApplicationBaseManager(PageQuerySet):
    def order_by_end_date(self):
        # OutRef path__startswith with find all descendants of the parent
        # We only have children, so no issues at this time
        rounds = RoundBase.objects.open().filter(path__startswith=OuterRef('path'))
        qs = self.public().live().annotate(end_date=Subquery(rounds.values('end_date')[:1]))
        return qs.order_by('end_date')


class ApplicationBase(EmailForm, WorkflowStreamForm):  # type: ignore
    is_createable = False

    # Adds validation around forms & workflows. Isn't on Workflow class due to not displaying workflow field on Round
    base_form_class = WorkflowFormAdminForm

    description = RichTextField(blank=True)
    image = models.ImageField(blank=True)

    reviewers = ParentalManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='%(class)s_reviewers',
        limit_choices_to=LIMIT_TO_REVIEWERS,
        blank=True,
    )

    approval_form = models.ForeignKey(
        'application_projects.ProjectApprovalForm',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='funds',
    )

    guide_link = models.URLField(blank=True, max_length=255, help_text=_('Link to the apply guide.'))

    slack_channel = models.CharField(blank=True, max_length=128, help_text=_('The slack #channel for notifications. If left empty, notifications will go to the default channel.'))

    objects = PageManager.from_queryset(ApplicationBaseManager)()

    parent_page_types = ['apply_home.ApplyHomePage']

    def get_template(self, request, *args, **kwargs):
        # We want to force children to use our base template
        # template attribute is ignored by children
        return 'funds/application_base.html'

    def detail(self):
        # The location to find out more information
        return self.application_public.first()

    @cached_property
    def open_round(self):
        return RoundBase.objects.child_of(self).open().first()

    def next_deadline(self):
        try:
            return self.open_round.end_date
        except AttributeError:
            # There isn't an open round
            return None

    def serve(self, request):
        if hasattr(request, 'is_preview') or not self.open_round:
            return super().serve(request)

        # delegate to the open_round to use the latest form instances
        request.show_round = True
        return self.open_round.serve(request)

    content_panels = WorkflowStreamForm.content_panels + [
        FieldPanel('approval_form'),
        FieldPanel('reviewers', widget=forms.SelectMultiple(attrs={'size': '16'})),
        FieldPanel('guide_link'),
        FieldPanel('description'),
        FieldPanel('image'),
        FieldPanel('slack_channel'),
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading=_('Content')),
        EmailForm.email_tab,
        ObjectList(WorkflowStreamForm.promote_panels, heading=_('Promote')),
    ])


class RoundBaseManager(PageQuerySet):
    def open(self):
        rounds = self.live().public().specific()
        rounds = rounds.filter(
            Q(start_date__lte=date.today()) &
            Q(Q(end_date__isnull=True) | Q(end_date__gte=date.today()))
        )
        return rounds

    def closed(self):
        rounds = self.live().public().specific()
        rounds = rounds.filter(end_date__lt=date.today())
        return rounds


class RoundBase(WorkflowStreamForm, SubmittableStreamForm):  # type: ignore
    is_creatable = False
    submission_class = ApplicationSubmission

    objects = PageManager.from_queryset(RoundBaseManager)()

    subpage_types = []  # type: ignore

    # Adds validation for making start_date required
    base_form_class = RoundBasePageAdminForm

    lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        limit_choices_to=LIMIT_TO_STAFF,
        related_name='%(class)s_lead',
        on_delete=models.PROTECT,
    )
    reviewers = ParentalManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='%(class)s_reviewer',
        limit_choices_to=LIMIT_TO_REVIEWERS,
        blank=True,
    )
    start_date = models.DateField(null=True, blank=True, default=date.today)
    end_date = models.DateField(
        blank=True,
        null=True,
        default=date.today,
        help_text=_('When no end date is provided the round will remain open indefinitely.')
    )
    sealed = models.BooleanField(default=False)

    content_panels = SubmittableStreamForm.content_panels + [
        FieldPanel('lead'),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('start_date'),
                FieldPanel('end_date'),
            ]),
        ], heading=_('Dates')),
        FieldPanel('reviewers', widget=forms.SelectMultiple(attrs={'size': '16'})),
        ReadOnlyPanel('get_workflow_name_display', heading=_('Workflow'), help_text=_('Copied from the fund.')),
        # Forms comes from parental key in models/forms.py
        ReadOnlyInlinePanel('forms', help_text=_('Copied from the fund.')),
        ReadOnlyInlinePanel('review_forms', help_text=_('Copied from the fund.')),
        ReadOnlyInlinePanel('determination_forms', help_text=_('Copied from the fund.')),
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading=_('Content')),
        ObjectList(SubmittableStreamForm.promote_panels, heading=_('Promote')),
    ])

    def get_template(self, request, *args, **kwargs):
        # Make sure all children use the shared template
        return 'funds/round.html'

    def get_landing_page_template(self, request, *args, **kwargs):
        # Make sure all children use the shared template
        return 'funds/round_landing.html'

    @cached_property
    def fund(self):
        return self.get_parent()

    @property
    def is_sealed(self):
        return self.sealed and self.is_open

    @property
    def is_open(self):
        return self.start_date <= date.today() <= self.end_date

    def save(self, *args, **kwargs):
        is_new = not self.id
        if is_new and hasattr(self, 'parent_page'):
            parent_page = self.parent_page[self.__class__][self.title]
            self.workflow_name = parent_page.workflow_name
            self.reviewers = parent_page.reviewers.all()

        super().save(*args, **kwargs)

        if is_new and hasattr(self, 'parent_page'):
            # Would be nice to do this using model clusters as part of the __init__
            self._copy_forms('forms')
            self._copy_forms('review_forms')
            self._copy_forms('determination_forms')

    def _copy_forms(self, field):
        for form in getattr(self.get_parent().specific, field).all():
            new_form = self._meta.get_field(field).related_model
            self._copy_form(form, new_form)

    def _copy_form(self, form, new_class):
        # Create a copy of the existing form object
        new_form = form.form
        new_form.id = None
        new_form.name = '{} for {} ({})'.format(new_form.name, self.title, self.get_parent().title)
        new_form.save()
        if hasattr(form, 'stage'):
            new_class.objects.create(round=self, form=new_form, stage=form.stage)
        else:
            new_class.objects.create(round=self, form=new_form)

    def get_submit_meta_data(self, **kwargs):
        return super().get_submit_meta_data(
            page=self.get_parent(),
            round=self,
            **kwargs,
        )

    def clean(self):
        super().clean()

        conflict_query = ()

        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError({
                'end_date': 'End date must come after the start date',
            })

        if self.start_date and self.end_date:
            conflict_query = (
                Q(start_date__range=[self.start_date, self.end_date]) |
                Q(end_date__range=[self.start_date, self.end_date]) |
                Q(start_date__lte=self.start_date, end_date__gte=self.end_date)
            )
        elif self.start_date:
            conflict_query = (
                Q(start_date__lte=self.start_date, end_date__isnull=True) |
                Q(end_date__gte=self.start_date)
            )

        if not self.id and hasattr(self, 'parent_page'):
            # Check if the create hook has added the parent page, we aren't an object yet.
            # Ensures we can access related objects during the clean phase instead of save.
            base_query = RoundBase.objects.child_of(self.parent_page[self.__class__][self.title])
        else:
            # don't need parent page, we are an actual object now.
            base_query = RoundBase.objects.sibling_of(self)

        if conflict_query:
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

    def get_initial_data_open_call_submission(self, submission_id):
        initial_values = {}

        try:
            submission_class = self.get_submission_class()
            submission = submission_class.objects.get(id=submission_id)
            if submission.status in OPEN_CALL_PHASES and self.get_parent() == submission.page:
                title_block_id = submission.named_blocks.get('title')
                if title_block_id:
                    field_data = submission.data(title_block_id)
                    initial_values[title_block_id] = field_data + ' (please edit)'

                for field_id in submission.first_group_normal_text_blocks:
                    field_data = submission.data(field_id)
                    initial_values[field_id] = field_data

                # Select first item in the Group toggle blocks
                for toggle_block_id, toggle_field in submission.group_toggle_blocks:
                    try:
                        initial_values[toggle_block_id] = toggle_field.value['choices'][0]
                    except IndexError:
                        initial_values[toggle_block_id] = 'yes'
                    except KeyError:
                        pass

        except (submission_class.DoesNotExist, ValueError):
            pass

        return initial_values

    def get_form_parameters(self, submission_id=None):
        form_parameters = {}

        if submission_id:
            initial_values = self.get_initial_data_open_call_submission(submission_id)
            if initial_values:
                form_parameters['initial'] = initial_values

        return form_parameters

    def get_form(self, *args, **kwargs):
        draft = kwargs.pop('draft', False)
        try:
            form_class = self.get_form_class(draft, args[0])
        except IndexError:
            form_class = self.get_form_class(draft)
        submission_id = kwargs.pop('submission_id', None)
        form_params = self.get_form_parameters(submission_id=submission_id)
        form_params.update(kwargs)
        return form_class(*args, **form_params)

    def serve(self, request, *args, **kwargs):
        if hasattr(request, 'is_preview') or hasattr(request, 'show_round'):
            # Overriding serve method to pass submission id to get_form method
            copy_open_submission = request.GET.get('open_call_submission')
            if request.method == 'POST':
                draft = request.POST.get('draft', False)
                form = self.get_form(request.POST, request.FILES, page=self, user=request.user, draft=draft)

                if form.is_valid():
                    form_submission = self.process_form_submission(form, draft=draft)
                    # Required for django-file-form: delete temporary files for the new files
                    # that are uploaded.
                    form.delete_temporary_files()
                    return self.render_landing_page(request, form_submission, *args, **kwargs)
            else:
                form = self.get_form(page=self, user=request.user, submission_id=copy_open_submission)

            context = self.get_context(request)
            context['form'] = form
            context['show_all_group_fields'] = True if copy_open_submission else False
            return render(
                request,
                self.get_template(request),
                context
            )

        # We hide the round as only the open round is used which is displayed through the
        # fund page
        raise Http404()


class LabBase(EmailForm, WorkflowStreamForm, SubmittableStreamForm):  # type: ignore
    is_createable = False
    submission_class = ApplicationSubmission

    # Adds validation around forms & workflows.
    base_form_class = WorkflowFormAdminForm
    description = RichTextField(blank=True)
    image = models.ImageField(blank=True)
    lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        limit_choices_to=LIMIT_TO_STAFF,
        related_name='lab_lead',
        on_delete=models.PROTECT,
    )
    reviewers = ParentalManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='labs_reviewer',
        limit_choices_to=LIMIT_TO_REVIEWERS,
        blank=True,
    )

    approval_form = models.ForeignKey(
        'application_projects.ProjectApprovalForm',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='labs',
    )

    guide_link = models.URLField(blank=True, max_length=255, help_text=_('Link to the apply guide.'))

    slack_channel = models.CharField(blank=True, max_length=128, help_text=_('The slack #channel for notifications.'))

    parent_page_types = ['apply_home.ApplyHomePage']
    subpage_types = []  # type: ignore

    content_panels = WorkflowStreamForm.content_panels + [
        FieldPanel('approval_form'),
        FieldPanel('lead'),
        FieldPanel('reviewers', widget=forms.SelectMultiple(attrs={'size': '16'})),
        FieldPanel('guide_link'),
        FieldPanel('description'),
        FieldPanel('image'),
        FieldPanel('slack_channel'),
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading=_('Content')),
        EmailForm.email_tab,
        ObjectList(WorkflowStreamForm.promote_panels, heading=_('Promote')),
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

    def serve(self, request, *args, **kwargs):
        if request.method == 'POST':
            form = self.get_form(request.POST, request.FILES, page=self, user=request.user)
            draft = request.POST.get('draft', False)
            if form.is_valid():
                form_submission = SubmittableStreamForm.process_form_submission(self, form, draft=draft)
                return self.render_landing_page(request, form_submission, *args, **kwargs)
        else:
            form = self.get_form(page=self, user=request.user)

        context = self.get_context(request)
        context['form'] = form
        return TemplateResponse(
            request,
            self.get_template(request),
            context
        )


class RoundsAndLabsQueryset(PageQuerySet):
    def new(self):
        return self.filter(start_date__gt=date.today())

    def open(self):
        return self.filter(Q(end_date__gte=date.today(), start_date__lte=date.today()) | Q(end_date__isnull=True))

    def closed(self):
        return self.filter(end_date__lt=date.today())

    def by_lead(self, user):
        return self.filter(lead_pk=user.pk)


class RoundsAndLabsProgressQueryset(RoundsAndLabsQueryset):
    def active(self):
        return self.filter(progress__lt=100)

    def inactive(self):
        return self.filter(progress=100)


class RoundsAndLabsManager(PageManager):
    def get_queryset(self, base_queryset=RoundsAndLabsQueryset):
        funds = ApplicationBase.objects.filter(path=OuterRef('parent_path'))

        return base_queryset(self.model, using=self._db).type(SubmittableStreamForm).annotate(
            lead=Coalesce(
                F('roundbase__lead__full_name'),
                F('labbase__lead__full_name'),
            ),
            start_date=F('roundbase__start_date'),
            end_date=F('roundbase__end_date'),
            parent_path=Left(F('path'), Length('path') - ApplicationBase.steplen, output_field=CharField()),
            fund=Subquery(funds.values('title')[:1]),
            lead_pk=Coalesce(
                F('roundbase__lead__pk'),
                F('labbase__lead__pk'),
            ),
        )

    def with_progress(self):
        submissions = ApplicationSubmission.objects.filter(Q(round=OuterRef('pk')) | Q(page=OuterRef('pk'))).current()
        closed_submissions = submissions.inactive()

        return self.get_queryset(RoundsAndLabsProgressQueryset).annotate(
            total_submissions=Coalesce(
                Subquery(
                    submissions.values('round').annotate(count=Count('pk')).values('count'),
                    output_field=IntegerField(),
                ),
                0,
            ),
            closed_submissions=Coalesce(
                Subquery(
                    closed_submissions.values('round').annotate(count=Count('pk')).values('count'),
                    output_field=IntegerField(),
                ),
                0,
            ),
        ).annotate(
            progress=Case(
                When(total_submissions=0, then=None),
                default=(F('closed_submissions') * 100) / F('total_submissions'),
                output_fields=FloatField(),
            )

        )

    def open(self):
        return self.get_queryset().open()

    def closed(self):
        return self.get_queryset().closed()

    def new(self):
        return self.get_queryset().new()

    def by_lead(self, user):
        return self.get_queryset().by_lead(user)


class RoundsAndLabs(Page):
    """
    This behaves as a useful way to get all the rounds and labs that are defined
    in the project regardless of how they are implemented (lab/round/sealed_round)
    """
    class Meta:
        proxy = True

    def __eq__(self, other):
        # This is one way equality RoundAndLab == Round/Lab
        # Round/Lab == RoundAndLab returns False due to different
        # Concrete class
        if not isinstance(other, models.Model):
            return False
        if not isinstance(other, SubmittableStreamForm):
            return False
        my_pk = self.pk
        if my_pk is None:
            return self is other
        return my_pk == other.pk

    objects = RoundsAndLabsManager()

    def save(self, *args, **kwargs):
        raise NotImplementedError('Do not save through this model')


@register_setting
class ApplicationSettings(BaseSetting):
    class Meta:
        verbose_name = 'application settings'

    extra_text_round = RichTextField(blank=True)
    extra_text_lab = RichTextField(blank=True)

    panels = [
        MultiFieldPanel([
            FieldPanel('extra_text_round'),
            FieldPanel('extra_text_lab'),
        ], 'extra text on application landing page'),
    ]
