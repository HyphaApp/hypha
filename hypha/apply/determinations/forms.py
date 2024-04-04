from collections import OrderedDict

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import NON_FIELD_ERRORS
from django.utils.translation import gettext_lazy as _

from hypha.apply.funds.models import ApplicationSubmission
from hypha.apply.stream_forms.forms import StreamBaseForm
from hypha.apply.utils.fields import RichTextField

from .models import Determination, DeterminationFormSettings
from .options import DETERMINATION_CHOICES, TRANSITION_DETERMINATION
from .utils import determination_actions

User = get_user_model()


class BaseDeterminationForm:
    def __init__(self, *args, user, initial, action, edit=False, **kwargs):
        if "site" in kwargs:
            site = kwargs.pop("site")
            self.form_settings = DeterminationFormSettings.for_site(site)
        try:
            initial.update(outcome=TRANSITION_DETERMINATION[action])
        except KeyError:
            pass
        initial.update(author=user.id)
        super().__init__(*args, initial=initial, **kwargs)

    def data_fields(self):
        return []

    def clean_outcome(self):
        # Enforce outcome as an int
        return int(self.cleaned_data["outcome"])

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data["data"] = {
            key: value
            for key, value in cleaned_data.items()
            if key in self.data_fields()
        }
        return cleaned_data

    def apply_form_settings(self, application_type, fields):
        for field in fields:
            try:
                self.fields[field].label = getattr(
                    self.form_settings, f"{application_type}_{field}_label"
                )
            except AttributeError:
                pass
            try:
                self.fields[field].help_text = getattr(
                    self.form_settings, f"{application_type}_{field}_help_text"
                )
            except AttributeError:
                pass
        return fields

    @classmethod
    def get_detailed_response(cls, saved_data):
        data = {}
        for group, title in cls.titles.items():
            data.setdefault(group, {"title": title, "questions": []})

        for name, field in cls.base_fields.items():
            try:
                value = saved_data[name]
            except KeyError:
                # The field is not stored in the data
                pass
            else:
                data[field.group]["questions"].append((field.label, str(value)))

        return data


class BaseNormalDeterminationForm(BaseDeterminationForm, forms.ModelForm):
    draft_button_name = "save_draft"

    class Meta:
        model = Determination
        fields = ["outcome", "message", "submission", "author", "data", "send_notice"]

        widgets = {
            "submission": forms.HiddenInput(),
            "author": forms.HiddenInput(),
            "data": forms.HiddenInput(),
        }

        error_messages = {
            NON_FIELD_ERRORS: {
                "unique_together": "You have already created a determination for this submission",
            }
        }

    def data_fields(self):
        return [field for field in self.fields if field not in self._meta.fields]

    def outcome_choices_for_phase(self, submission, user):
        """
        Outcome choices correspond to Phase transitions.
        We need to filter out non-matching choices.
        i.e. a transition to In Review is not a determination, while Needs more info or Rejected are.
        """
        available_choices = [("", _("-- No determination selected -- "))]
        choices = dict(self.fields["outcome"].choices)

        for transition_name in determination_actions(user, submission):
            try:
                determination_type = TRANSITION_DETERMINATION[transition_name]
            except KeyError:
                pass
            else:
                available_choices.append(
                    (determination_type, choices[determination_type])
                )
        return available_choices

    def save(self, commit=True):
        self.instance.is_draft = self.draft_button_name in self.data

        return super().save(commit)


class BaseBatchDeterminationForm(BaseDeterminationForm, forms.Form):
    submissions = forms.ModelMultipleChoiceField(
        queryset=ApplicationSubmission.objects.all(),
        widget=forms.ModelMultipleChoiceField.hidden_widget,
    )
    author = forms.ModelChoiceField(
        # Permissions should be handled by the view rather than the QuerySet here.
        queryset=User.objects.active(),
        widget=forms.ModelChoiceField.hidden_widget,
        required=True,
    )

    def data_fields(self):
        return [
            field
            for field in self.fields
            if field
            not in ["submissions", "outcome", "author", "send_notice", "message"]
        ]

    def _post_clean(self):
        submissions = self.cleaned_data["submissions"].undetermined()
        data = {
            field: self.cleaned_data[field]
            for field in ["author", "data", "outcome", "message"]
        }

        self.instances = [
            Determination(
                submission=submission,
                **data,
            )
            for submission in submissions
        ]

        return super()._post_clean()

    def save(self):
        determinations = Determination.objects.bulk_create(self.instances)
        self.instances = determinations
        return determinations


class BaseConceptDeterminationForm(forms.Form):
    titles = {
        1: "Feedback",
    }
    outcome = forms.ChoiceField(
        choices=DETERMINATION_CHOICES,
        label=_("Determination"),
        help_text="Do you recommend requesting a proposal based on this concept note?",
    )
    outcome.group = 1

    message = RichTextField(
        label=_("Determination message"),
        help_text="This text will be e-mailed to the applicant. "
        "Ones when text is first added and then every time the text is changed.",
    )
    message.group = 1

    principles = RichTextField(
        label=_("Goals and principles"),
        help_text="Does the project contribute and/or have relevance to OTF goals and principles?"
        "Are the goals and objectives of the project clear? Is it a technology research, development, or deployment "
        "project? Can project’s effort be explained to external audiences and non-technical people? What problem are "
        "they trying to solve and is the solution strategical or tactical? Is the project strategically or tactically "
        "important to OTF’s goals, principles and rationale and other OTF efforts? Is it clear how? What tools, if any, "
        "currently exist to solve this problem? How is this project different? Does the effort have any overlap with "
        "existing OTF and/or USG supported projects? Is the overlap complementary or duplicative? If complementary, "
        "can it be explained clearly? I.e. geographic focus, technology, organization profile, etc. What are the "
        "liabilities and risks of taking on this project? I.e. political personalities, financial concerns, technical "
        "controversial, etc. Is the organization or its members known within any relevant communities? If yes, what is "
        "their reputation and why? What is the entity’s motivation and principles? What are the entity member(s) "
        "motivations and principles? Where is the organization physically and legally based? If the organization is "
        "distributed, where is the main point of contact? Does the organization have any conflicts of interest with "
        "RFA, OTF, the Advisory Council, or other RFA-OTF projects? Is the project team an organization, community "
        "or an individual?",
    )
    principles.group = 1

    technical = RichTextField(
        label=_("Technical merit"),
        help_text="Does the project clearly articulate the technical problem, solution, and approach? "
        "Is the problem clearly justifiable? Does the project clearly articulate the technological objectives? "
        "Is it an open or closed development project? I.e. Open source like Android or open source like Firefox OS "
        "or closed like iOS. Does a similar technical solution already exist? If so, what are the differentiating "
        "factors? Is the effort to sustain an existing technical approach? If so, are these considered successful? "
        "Is the effort a new technical approach or improvement to an existing solution? If so, how? Is the effort "
        "a completely new technical approach fostering new solutions in the field? Does the project’s technical "
        "approach solve the problem? What are the limitations of the project’s technical approach and solution? "
        "What are the unintended or illicit uses and consequences of this technology? Has the project identified "
        "and/or developed any safeguards for these consequences?",
    )
    technical.group = 1

    sustainable = RichTextField(
        label=_("Reasonable, realistic and sustainable"),
        help_text="Is the requested amount reasonable, realistic, and justified? If OTF doesn’t support the project, "
        "is it likely to be realized? Does the project provide a detailed and realistic description of effort and "
        "schedule? I.e. is the project capable of creating a work plan including objectives, activities, and "
        "deliverable(s)? Does the project have a clear support model? Is there a known sustainability plan for the "
        "future? What in-kind support or other revenue streams is the project receiving? I.e. volunteer developers, "
        "service or product sales. Is the project receiving any financial support from the USG? Is this information "
        "disclosed? Is the project receiving any other financial support? Is this information disclosed? Are existing "
        "supporters approachable? Are they likely aware and/or comfortable with the Intellectual property language "
        "within USG contracts?",
    )
    sustainable.group = 1

    comments = RichTextField(label=_("Other comments"), help_text="")
    comments.group = 1


class BaseProposalDeterminationForm(forms.Form):
    titles = {
        1: "A. Determination",
        2: "B. General thoughts",
        3: "C. Specific aspects",
        4: "D. Rationale and appropriateness consideration",
        5: "E. General recommendation",
    }

    # A. Determination

    outcome = forms.ChoiceField(
        choices=DETERMINATION_CHOICES,
        label=_("Determination"),
        help_text="Do you recommend requesting a proposal based on this concept note?",
    )
    outcome.group = 1

    message = RichTextField(
        label=_("Determination message"),
        help_text="This text will be e-mailed to the applicant. "
        "Ones when text is first added and then every time the text is changed.",
    )
    message.group = 1

    # B. General thoughts
    liked = RichTextField(
        label=_("Positive aspects"),
        help_text="Any general or specific aspects that got you really excited or that you like about this proposal.",
    )
    liked.group = 2

    concerns = RichTextField(
        label=_("Concerns"),
        help_text="Any general or specific aspects that concern you or leave you feeling uneasy about this proposal.",
    )
    concerns.group = 2

    red_flags = RichTextField(
        label=_("Items that must be addressed"),
        help_text="Anything you think should be flagged for our attention.",
    )
    red_flags.group = 2

    # C. Specific aspects
    overview = RichTextField(label=_("Project overview questions and comments"))
    overview.group = 3

    objectives = RichTextField(label=_("Objectives questions and comments"))
    objectives.group = 3

    strategy = RichTextField(label=_("Methods and strategy questions and comments"))
    strategy.group = 3

    technical = RichTextField(label=_("Technical feasibility questions and comments"))
    technical.group = 3

    alternative = RichTextField(
        label=_('Alternative analysis - "red teaming" questions and comments')
    )
    alternative.group = 3

    usability = RichTextField(label=_("Usability questions and comments"))
    usability.group = 3

    sustainability = RichTextField(label=_("Sustainability questions and comments"))
    sustainability.group = 3

    collaboration = RichTextField(label=_("Collaboration questions and comments"))
    collaboration.group = 3

    realism = RichTextField(label=_("Cost realism questions and comments"))
    realism.group = 3

    qualifications = RichTextField(label=_("Qualifications questions and comments"))
    qualifications.group = 3

    evaluation = RichTextField(label=_("Evaluation questions and comments"))
    evaluation.group = 3

    # D. Rationale and appropriateness consideration
    rationale = RichTextField(
        label=_("Rationale and appropriateness questions and comments")
    )
    rationale.group = 4


class ConceptDeterminationForm(
    BaseConceptDeterminationForm, BaseNormalDeterminationForm
):
    def __init__(
        self, *args, submission, user, edit=False, initial=None, instance=None, **kwargs
    ):
        initial = initial or {}
        initial.update(submission=submission.id)

        if instance:
            for key, value in instance.data.items():
                if key not in self._meta.fields:
                    initial[key] = value

        super(BaseNormalDeterminationForm, self).__init__(
            *args, initial=initial, user=user, instance=instance, edit=edit, **kwargs
        )

        # convert a python dict to orderedDict, to use move_to_end method
        self.fields = OrderedDict(self.fields)

        for field in self._meta.widgets:
            self.fields[field].disabled = True

        self.fields["outcome"].choices = self.outcome_choices_for_phase(
            submission, user
        )

        if self.draft_button_name in self.data:
            for field in self.fields.values():
                field.required = False

        self.fields = self.apply_form_settings("concept", self.fields)
        self.fields.move_to_end("send_notice")

        action = kwargs.get("action")
        stages_num = len(submission.workflow.stages)

        if stages_num > 1:
            second_stage_forms = submission.get_from_parent("forms").filter(stage=2)
            if second_stage_forms.count() > 1:
                proposal_form_choices = [
                    (index, form.form.name)
                    for index, form in enumerate(second_stage_forms)
                ]
                proposal_form_choices.insert(
                    0, ("", _("-- No proposal form selected -- "))
                )
                proposal_form_help_text = _(
                    "Select the proposal form only for determination approval"
                )
                if action == "invited_to_proposal":
                    proposal_form_help_text = _(
                        "Select the proposal form to use for proposal stage."
                    )
                self.fields["proposal_form"] = forms.ChoiceField(
                    label=_("Proposal Form"),
                    choices=proposal_form_choices,
                    help_text=proposal_form_help_text,
                    required=True if action == "invited_to_proposal" else False,
                    disabled=False if action == "invited_to_proposal" else True,
                )
                self.fields["proposal_form"].group = 1
                self.fields.move_to_end("proposal_form", last=False)

        if edit:
            self.fields.pop("outcome")
            self.draft_button_name = None


class ProposalDeterminationForm(
    BaseProposalDeterminationForm, BaseNormalDeterminationForm
):
    def __init__(
        self, *args, submission, user, edit=False, initial=None, instance=None, **kwargs
    ):
        if initial is None:
            initial = {}
        initial.update(submission=submission.id)

        if instance:
            for key, value in instance.data.items():
                if key not in self._meta.fields:
                    initial[key] = value

        super(BaseNormalDeterminationForm, self).__init__(
            *args, initial=initial, user=user, instance=instance, edit=edit, **kwargs
        )

        # convert a python dict to orderedDict, to use move_to_end method
        self.fields = OrderedDict(self.fields)

        for field in self._meta.widgets:
            self.fields[field].disabled = True

        self.fields["outcome"].choices = self.outcome_choices_for_phase(
            submission, user
        )
        self.fields.move_to_end("send_notice")

        if self.draft_button_name in self.data:
            for field in self.fields.values():
                field.required = False

        self.fields = self.apply_form_settings("proposal", self.fields)

        if edit:
            self.fields.pop("outcome")
            self.draft_button_name = None


class BatchConceptDeterminationForm(
    BaseConceptDeterminationForm, BaseBatchDeterminationForm
):
    def __init__(self, *args, submissions, initial=None, **kwargs):
        if initial is None:
            initial = {}
        initial.update(submissions=submissions.values_list("id", flat=True))
        super(BaseBatchDeterminationForm, self).__init__(
            *args, initial=initial, **kwargs
        )
        self.fields["outcome"].widget = forms.HiddenInput()

        self.fields = self.apply_form_settings("concept", self.fields)


class BatchProposalDeterminationForm(
    BaseProposalDeterminationForm, BaseBatchDeterminationForm
):
    def __init__(self, *args, submissions, initial=None, **kwargs):
        if initial is None:
            initial = {}
        initial.update(submissions=submissions.values_list("id", flat=True))
        super(BaseBatchDeterminationForm, self).__init__(
            *args, initial=initial, **kwargs
        )
        self.fields["outcome"].widget = forms.HiddenInput()

        self.fields = self.apply_form_settings("proposal", self.fields)


class MixedMetaClass(type(StreamBaseForm), type(forms.ModelForm)):
    pass


class DeterminationModelForm(StreamBaseForm, forms.ModelForm, metaclass=MixedMetaClass):
    draft_button_name = "save draft"

    class Meta:
        model = Determination
        fields = ["outcome", "message", "submission", "author", "send_notice"]

        widgets = {
            "outcome": forms.HiddenInput(),
            "message": forms.HiddenInput(),
            "submission": forms.HiddenInput(),
            "author": forms.HiddenInput(),
            "send_notice": forms.HiddenInput(),
        }

        error_messages = {
            NON_FIELD_ERRORS: {
                "unique_together": "You have already created a determination for this submission",
            }
        }

    def __init__(
        self,
        *args,
        submission,
        action,
        user=None,
        edit=False,
        initial=None,
        instance=None,
        site=None,
        **kwargs,
    ):
        if initial is None:
            initial = {}
        initial.update(submission=submission.id)
        initial.update(author=user.id)
        if instance:
            for key, value in instance.form_data.items():
                if key not in self._meta.fields:
                    initial[key] = value
        super().__init__(*args, initial=initial, instance=instance, **kwargs)

        for field in self._meta.widgets:
            # Need to disable the model form fields as these fields would be
            # rendered via streamfield form.
            self.fields[field].disabled = True

        if self.draft_button_name in self.data:
            # A determination must be set for saving a draft,
            # this forces outcome to be validated.
            unreq_fields = [name for name in self.fields if name != "outcome"]
            for name in unreq_fields:
                self.fields[name].required = False

        if edit:
            self.fields.pop("outcome")
            self.draft_button_name = None

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data["form_data"] = {
            key: value
            for key, value in cleaned_data.items()
            if key not in self._meta.fields
        }

        return cleaned_data

    def save(self, commit=True):
        self.instance.send_notice = (
            self.cleaned_data[self.instance.send_notice_field.id]
            if self.instance.send_notice_field
            else True
        )
        self.instance.message = self.cleaned_data[self.instance.message_field.id]
        try:
            self.instance.outcome = int(
                self.cleaned_data[self.instance.determination_field.id]
            )
        except KeyError:
            # Need to catch KeyError as outcome field would not exist in case of edit.
            pass
        self.instance.is_draft = self.draft_button_name in self.data
        self.instance.form_data = self.cleaned_data["form_data"]
        return super().save(commit)


class FormMixedMetaClass(type(StreamBaseForm), type(forms.Form)):
    pass


class BatchDeterminationForm(StreamBaseForm, forms.Form, metaclass=FormMixedMetaClass):
    submissions = forms.ModelMultipleChoiceField(
        queryset=ApplicationSubmission.objects.all(),
        widget=forms.ModelMultipleChoiceField.hidden_widget,
    )
    author = forms.ModelChoiceField(
        # Permissions should be handled by the view rather than the QuerySet here.
        queryset=User.objects.active(),
        widget=forms.ModelChoiceField.hidden_widget,
        required=True,
    )
    outcome = forms.ChoiceField(
        choices=DETERMINATION_CHOICES,
        label=_("Determination"),
        help_text="Do you recommend requesting a proposal based on this concept note?",
        widget=forms.HiddenInput(),
    )

    def __init__(
        self,
        *args,
        user,
        submissions,
        action,
        initial=None,
        edit=False,
        site=None,
        **kwargs,
    ):
        if initial is None:
            initial = {}
        initial.update(submissions=submissions.values_list("id", flat=True))
        try:
            initial.update(outcome=TRANSITION_DETERMINATION[action])
        except KeyError:
            pass
        initial.update(author=user.id)
        super().__init__(*args, initial=initial, **kwargs)
        self.fields["submissions"].disabled = True
        self.fields["author"].disabled = True
        self.fields["outcome"].disabled = True

    def data_fields(self):
        return [
            field
            for field in self.fields
            if field not in ["submissions", "outcome", "author", "send_notice"]
        ]

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data["form_data"] = {
            key: value
            for key, value in cleaned_data.items()
            if key in self.data_fields()
        }
        return cleaned_data

    def clean_outcome(self):
        # Enforce outcome as an int
        return int(self.cleaned_data["outcome"])

    def _post_clean(self):
        submissions = self.cleaned_data["submissions"].undetermined()
        data = {
            # If one of these keys is not set, we should get a validation error on the page rather than `KeyError`.
            field: self.cleaned_data.get(field)
            for field in ["author", "form_data", "outcome"]
        }

        self.instances = [
            Determination(
                submission=submission,
                **data,
            )
            for submission in submissions
        ]

        return super()._post_clean()

    def save(self):
        determinations = Determination.objects.bulk_create(self.instances)
        self.instances = determinations
        return determinations
