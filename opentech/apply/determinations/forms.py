from django import forms
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django_fsm import can_proceed

from opentech.apply.funds.workflow import DETERMINATION_RESPONSE_TRANSITIONS
from .models import Determination, DETERMINATION_CHOICES, UNDETERMINED, UNAPPROVED, APPROVED

from opentech.apply.utils.options import RICH_TEXT_WIDGET


class RichTextField(forms.CharField):
    widget = RICH_TEXT_WIDGET

    def __init__(self, *args, required=False, **kwargs):
        kwargs.update(required=required)
        super().__init__(*args, **kwargs)


class RequiredRichTextField(forms.CharField):
    widget = RICH_TEXT_WIDGET


class BaseDeterminationForm(forms.ModelForm):
    draft_button_name = "save_draft"

    class Meta:
        model = Determination
        fields: list = []

        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together': "You have already created a determination for this submission",
            }
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.submission = kwargs.pop('submission')
        self.transition = None
        super().__init__(*args, **kwargs)

        self.fields['determination'].initial = self.get_determination_default()

        if self.draft_button_name in self.data:
            for field in self.fields.values():
                field.required = False

    def validate_unique(self):
        # update the instance data prior to validating uniqueness
        self.instance.submission = self.submission
        self.instance.author = self.request.user
        self.instance.determination_data = {key: value for key, value in self.cleaned_data.items()
                                            if key not in ['determination', 'determination_message']}

        try:
            self.instance.validate_unique()
        except ValidationError as e:
            self._update_errors(e)

    def clean(self):
        cleaned_data = super().clean()

        if not self.draft_button_name in self.data:
            action_name = self.request.GET.get('action')
            if not action_name:
                # The action name was not passed as a request parameter, so derive it
                # from the determination and submission status
                suffix = '_more_info'
                if cleaned_data['determination'] == APPROVED:
                    suffix = '_accepted'
                elif cleaned_data['determination'] == UNAPPROVED:
                    suffix = '_rejected'

                # Use get_available_status_transitions()?
                for key, _ in self.submission.phase.transitions.items():
                    action_name = key if suffix in key else None

            if action_name:
                transition = self.submission.get_transition(action_name)
                if not can_proceed(transition):
                    action = self.submission.phase.transitions[action_name]
                    raise forms.ValidationError(f'You do not have permission to "{ action }"')

                self.transition = transition

        return cleaned_data

    def save(self, commit=True):
        self.instance.determination = int(self.cleaned_data['determination'])
        self.instance.determination_message = self.cleaned_data['determination_message']
        self.instance.is_draft = self.draft_button_name in self.data or self.instance.determination == UNDETERMINED
        self.instance.is_draft = True

        if self.transition:
            self.transition(by=self.request.user)
            self.submission.save()

        super().save(commit)

    def get_determination_default(self):
        action_name = self.request.GET.get('action')
        if action_name in DETERMINATION_RESPONSE_TRANSITIONS:
            if '_more_info' in action_name:
                return UNDETERMINED
            elif '_accepted' in action_name:
                return APPROVED
        return UNAPPROVED


class ConceptDeterminationForm(BaseDeterminationForm):
    determination = forms.ChoiceField(
        choices=DETERMINATION_CHOICES,
        label='Determination',
        help_text='Do you recommend requesting a proposal based on this concept note?',
    )
    determination_message = RichTextField(
        label='Determination message',
        help_text='This text will be e-mailed to the applicant. '
        'Ones when text is first added and then every time the text is changed.'
    )

    principles = RichTextField(
        label='Goals and principles',
        help_text='Does the project contribute and/or have relevance to OTF goals and principles?'
        'Are the goals and objectives of the project clear? Is it a technology research, development, or deployment '
        'project? Can project’s effort be explained to external audiences and non-technical people? What problem are '
        'they trying to solve and is the solution strategical or tactical? Is the project strategically or tactically '
        'important to OTF’s goals, principles and rationale and other OTF efforts? Is it clear how? What tools, if any, '
        'currently exist to solve this problem? How is this project different? Does the effort have any overlap with '
        'existing OTF and/or USG supported projects? Is the overlap complementary or duplicative? If complementary, '
        'can it be explained clearly? I.e. geographic focus, technology, organization profile, etc. What are the '
        'liabilities and risks of taking on this project? I.e. political personalities, financial concerns, technical '
        'controversial, etc. Is the organization or its members known within any relevant communities? If yes, what is '
        'their reputation and why? What is the entity’s motivation and principles? What are the entity member(s) '
        'motivations and principles? Where is the organization physically and legally based? If the organization is '
        'distributed, where is the main point of contact? Does the organization have any conflicts of interest with '
        'RFA, OTF, the Advisory Council, or other RFA-OTF projects? Is the project team an organization, community '
        'or an individual?'
    )

    technical = RichTextField(
        label='Technical merit',
        help_text='Does the project clearly articulate the technical problem, solution, and approach? '
        'Is the problem clearly justifiable? Does the project clearly articulate the technological objectives? '
        'Is it an open or closed development project? I.e. Open source like Android or open source like Firefox OS '
        'or closed like iOS. Does a similar technical solution already exist? If so, what are the differentiating '
        'factors? Is the effort to sustain an existing technical approach? If so, are these considered successful? '
        'Is the effort a new technical approach or improvement to an existing solution? If so, how? Is the effort '
        'a completely new technical approach fostering new solutions in the field? Does the project’s technical '
        'approach solve the problem? What are the limitations of the project’s technical approach and solution? '
        'What are the unintended or illicit uses and consequences of this technology? Has the project identified '
        'and/or developed any safeguards for these consequences?'
    )

    sustainable = RichTextField(
        label='Reasonable, realistic and sustainable',
        help_text='Is the requested amount reasonable, realistic, and justified? If OTF doesn’t support the project, '
        'is it likely to be realized? Does the project provide a detailed and realistic description of effort and '
        'schedule? I.e. is the project capable of creating a work plan including objectives, activities, and '
        'deliverable(s)? Does the project have a clear support model? Is there a known sustainability plan for the '
        'future? What in-kind support or other revenue streams is the project receiving? I.e. volunteer developers, '
        'service or product sales. Is the project receiving any financial support from the USG? Is this information '
        'disclosed? Is the project receiving any other financial support? Is this information disclosed? Are existing '
        'supporters approachable? Are they likely aware and/or comfortable with the Intellectual property language '
        'within USG contracts?'
    )

    # TODO option to not send message, or resend


class ProposalDeterminationForm(BaseDeterminationForm):
    titles = {
        1: 'A. Determination',
        2: 'B. General thoughts',
        3: 'C. Specific aspects',
        4: 'D. Rationale and appropriateness consideration',
        5: 'E. General recommendation',
    }

    # A. Determination

    determination = forms.ChoiceField(
        choices=DETERMINATION_CHOICES,
        label='Determination',
        help_text='Do you recommend requesting a proposal based on this concept note?'
    )
    determination.group = 1

    determination_message = RichTextField(
        label='Determination message',
        help_text='This text will be e-mailed to the applicant. '
        'Ones when text is first added and then every time the text is changed.'
    )
    determination_message.group = 1

    # B. General thoughts
    liked = RichTextField(
        label='Positive aspects',
        help_text='Any general or specific aspects that got you really excited or that you like about this proposal.'
    )
    liked.group = 2

    concerns = RichTextField(
        label='Concerns',
        help_text='Any general or specific aspects that concern you or leave you feeling uneasy about this proposal.'
    )
    concerns.group = 2

    red_flags = RichTextField(
        label='Items that must be addressed',
        help_text='Anything you think should be flagged for our attention.'
    )
    red_flags.group = 2

    # C. Specific aspects
    overview = RichTextField(label='Project overview questions and comments')
    overview.group = 3

    objectives = RichTextField(label='Objectives questions and comments')
    objectives.group = 3

    strategy = RichTextField(label='Methods and strategy questions and comments')
    strategy.group = 3

    technical = RichTextField(label='Technical feasibility questions and comments')
    technical.group = 3

    alternative = RichTextField(label='Alternative analysis - "red teaming" questions and comments')
    alternative.group = 3

    usability = RichTextField(label='Usability questions and comments')
    usability.group = 3

    sustainability = RichTextField(label='Sustainability questions and comments')
    sustainability.group = 3

    collaboration = RichTextField(label='Collaboration questions and comments')
    collaboration.group = 3

    realism = RichTextField(label='Cost realism questions and comments')
    realism.group = 3

    qualifications = RichTextField(label='Qualifications questions and comments')
    qualifications.group = 3

    evaluation = RichTextField(label='Evaluation questions and comments')
    evaluation.group = 3

    # D. Rationale and appropriateness consideration
    rationale = RichTextField(label='Rationale and appropriateness questions and comments')
    rationale.group = 4
