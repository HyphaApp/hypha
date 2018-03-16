from django import forms
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError

from tinymce.widgets import TinyMCE

from .models import Review, RECOMMENDATION_CHOICES

NA = 99

RATE_CHOICES = (
    (0, '0. Need more info'),
    (1, '1. Poor'),
    (2, '2. Not so good'),
    (3, '3. Is o.k.'),
    (4, '4. Good'),
    (5, '5. Excellent'),
    (NA, 'n/a - choose not to answer'),
)

YES_NO_CHOICES = (
    (1, 'Yes'),
    (0, 'No')
)

RICH_TEXT_WIDGET = TinyMCE(mce_attrs={
    'elementpath': False,
    'branding': False,
    'toolbar1': 'undo redo | styleselect | bold italic | bullist numlist | link',
    'style_formats': [
        {'title': 'Headers', 'items': [
            {'title': 'Header 1', 'format': 'h1'},
            {'title': 'Header 2', 'format': 'h2'},
            {'title': 'Header 3', 'format': 'h3'},
        ]},
        {'title': 'Inline', 'items': [
            {'title': 'Bold', 'icon': 'bold', 'format': 'bold'},
            {'title': 'Italic', 'icon': 'italic', 'format': 'italic'},
            {'title': 'Underline', 'icon': 'underline', 'format': 'underline'},
        ]},
    ],
})


class RichTextField(forms.CharField):
    widget = RICH_TEXT_WIDGET
    required = False


class RequiredRichTextField(RichTextField):
    required = True


class RateChoiceField(forms.ChoiceField):
    required = False

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.choices = RATE_CHOICES


class RequiredRateChoiceField(RateChoiceField):
    required = True


class BaseReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields: list = []

        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together': "You have already posted a review for this submission",
            }
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.submission = kwargs.pop('submission')
        super().__init__(*args, **kwargs)

    def validate_unique(self):
        # update the instance data prior to validating uniqueness
        self.instance.submission = self.submission
        self.instance.author = self.request.user
        self.instance.review = self.cleaned_data

        try:
            self.instance.validate_unique()
        except ValidationError as e:
            self._update_errors(e)

    def save(self, commit=True):
        self.instance.score = self.calculate_score()

        self.instance.recommendation = self.cleaned_data['recommendation']

        super().save()

    def calculate_score(self):
        scores = list()

        for field in self.get_score_fields():
            score = int(self.cleaned_data.get(field, NA))
            if score != NA:
                scores.append(score)

        return sum(scores) / len(scores)

    def get_score_fields(self):
        return [field for field in self.fields if field.endswith('_rate')]


class ConceptReviewForm(BaseReviewForm):
    recommendation = forms.ChoiceField(
        choices=RECOMMENDATION_CHOICES,
        label='Overall recommendation',
        help_text='Do you recommend requesting a proposal based on this concept note?'
    )
    recommendation_comments = RichTextField(label='Recommendation comments')

    principles = RichTextField(
        label='Goals and principles',
        help_text='Does the project contribute and/or have relevance to OTF goals and principles? '
        'Are the goals and objectives of the project clear? Is it a technology research, development, or deployment project? '
        'Can project’s effort be explained to external audiences and non-technical people? What problem are they '
        'trying to solve and is the solution strategical or tactical? Is the project strategically or tactically '
        'important to OTF’s goals, principles and rationale and other OTF efforts? Is it clear how? What tools, '
        'if any, currently exist to solve this problem? How is this project different? Does the effort have any '
        'overlap with existing OTF and/or USG supported projects? Is the overlap complementary or duplicative? '
        'If complementary, can it be explained clearly? I.e. geographic focus, technology, organization profile, etc. '
        'What are the liabilities and risks of taking on this project? I.e. political personalities, '
        'financial concerns, technical controversial, etc. Is the organization or its members known within any relevant '
        'communities? If yes, what is their reputation and why? What is the entity’s motivation and principles? '
        'What are the entity member(s) motivations and principles? Where is the organization physically and legally '
        'based? If the organization is distributed, where is the main point of contact? Does the organization have any '
        'conflicts of interest with RFA, OTF, the Advisory Council, or other RFA-OTF projects? Is the project team '
        'an organization, community or an individual?'
    )
    principles_rate = RequiredRateChoiceField(label='Rate goals and principles')

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
    technical_rate = RequiredRateChoiceField(label='Rate technical merit')

    sustainable = RichTextField(
        label='Reasonable and realistic',
        help_text='Is the requested amount reasonable, realistic, and justified? Does the project provide a detailed '
        'and realistic description of effort and schedule? I.e. is the project capable of creating a work plan '
        'including objectives, activities, and deliverable(s)?'
    )
    sustainable_rate = RequiredRateChoiceField(label='Rate reasonable and realistic')

    comments = RichTextField(label='General comments')
    request_questions = RichTextField(label='Request specific questions')


class ProposalReviewForm(BaseReviewForm):
    titles = {
        1: 'A. Conflicts of Interest and Confidentiality',
        2: 'B. General Thoughts',
        3: 'C. Specific aspects',
        4: 'D. Rationale and appropriateness consideration',
        5: 'E. General recommendation',
    }

    # A. Conflicts of Interest and Confidentiality
    confidentiality = forms.BooleanField(
        label='I understand about confidentiality',
        initial=False,
        help_text='I have reviewed and previously agreed to the RFA Council Confidentiality and Non-disclosure '
        'Agreement and I understand that the received proposal contains “Confidential Information” that may not be '
        'publicly known and shall not be disclosed to any third party.'
    )
    confidentiality.group = 1

    conflicts = forms.ChoiceField(
        widget=forms.RadioSelect(),
        choices=YES_NO_CHOICES,
        label='Do you have any conflicts of interest to report?'
    )
    conflicts.group = 1

    conflicts_disclosure = RichTextField(
        label='Conflict(s) of interest disclosure',
        help_text='If you checked yes, please list your conflict(s) of interest or potential conflict(s) of interest.'
    )
    conflicts_disclosure.group = 1

    # B. General thoughts
    liked = RichTextField(
        label='1. Positive aspects',
        help_text='Any general or specific aspects that got you really excited or that you like about this proposal.'
    )
    liked.group = 2

    concerns = RichTextField(
        label='2. Concerns',
        help_text='Any general or specific aspects that concern you or leave you feeling uneasy about this proposal.'
    )
    concerns.group = 2

    red_flags = RichTextField(
        label='3. Items that must be addressed',
        help_text='Any general or specific aspects that concern you or leave you feeling uneasy about this proposal.'
    )
    red_flags.group = 2

    # C. Specific aspects
    overview_rate = RequiredRateChoiceField(
        label='1. Project overview',
        help_text='Are the project’s goals clear? Are the project\'s goals realistically achievable by the proposed '
        'effort? Does the proposal identify and acknowledge what the challenges will be? Does the proposal state what '
        'is currently being done and the known limitations? Are project beneficiaries clear and specific? '
        'Is the project\'s sought after impact clear? Does the proposal cite an actual and compelling case study or '
        'user problem? Does the proposal state how much the effort will cost and how long will it take?'
    )
    overview_rate.group = 3

    overview = RichTextField(label='Project overview questions and comments')
    overview.group = 3

    objectives_rate = RequiredRateChoiceField(
        label='2. Proposal objectives',
        help_text='Does the proposal state a clear and concise set of objectives and tasks for the proposed effort? '
        'Are the objectives S.M.A.R.T. (Specific, Measurable, Achievable, Relevant, Timely)? Is the project responding '
        'to a potential need or function that is currently unfilled, or will it be duplicating previous efforts or '
        'creating a solution in search of a problem?'
    )
    objectives_rate.group = 3

    objectives = RichTextField(label='Objectives questions and comments')
    objectives.group = 3

    strategy_rate = RequiredRateChoiceField(
        label='3. Appropriate activities and strategy',
        help_text='Does the project propose activities that are appropriate for its goals and objectives? Does it '
        'demonstrate effectively how it will accomplish its stated activities? Does the proposal suggest alternative '
        'or modified activities in response to changing circumstances? Are the proposed activities viable in the real '
        'world? Do the project activities disrupt the current internet freedom context? Directly or indirectly, do '
        'they increase tactical breathing space for existing challenges? Are the activity\'s tactics clearly '
        'identifiable as part of a wider strategy?'
    )
    strategy_rate.group = 3

    strategy = RichTextField(label='Methods and strategy questions and comments')
    strategy.group = 3

    technical_rate = RequiredRateChoiceField(
        label='4. Technical feasibility (where applicable)',
        help_text='Does the proposal clearly state the effort\'s technical objectives? Are technical objectives '
        'articulated succinctly and with appropriate language? Does the proposal explain what is novel about its '
        'approach and why it will succeed? Does the project identify any hurdles to achieving technical objectives? '
        'Does the proposal recognize potential technical byproducts, such as new or increased attack surfaces?'
    )
    technical_rate.group = 3

    technical = RichTextField(label='Technical feasibility questions and comments')
    technical.group = 3

    alternative_rate = RequiredRateChoiceField(
        label='5. Alternative analysis - "red teaming"',
        help_text='Does the project identify potential unintended consequences? Does it identify how an adversary '
        'might use the solution to further their own goals? Does the proposal consider potential illicit uses of the '
        'project? Does the proposal identify appropriate tactics for a potentially asymmetric position in relation to '
        'an adversary? Does the proposal consider sufficiently whether its approach is offensive or defensive in '
        'relation to the problem it is addressing? Does it explain why it has selected this approach '
        '(effort, cost, time, etc.)? Does the proposal explore short-, medium-, and long‐term strategies from the '
        'adversary’s point of view? Does the project increase or decrease known attack surfaces? Does the proposal '
        'discuss how the project could be undermined, identify its own deficiencies and limitation, or does it presume there are none?'
    )
    alternative_rate.group = 3

    alternative = RichTextField(label='Alternative analysis - "red teaming" questions and comments')
    alternative.group = 3

    usability_rate = RequiredRateChoiceField(
        label='6. Usability',
        help_text='Does the proposal demonstrate clear external demand for the proposed end product? '
        'Does the project demonstrate a high degree of usability and/or accessibility? '
        'Is the project targeting a small number of high value or at-risk users, or a broader population? '
        'Is the proposed effort appropriate for the intended audience?'
    )
    usability_rate.group = 3

    usability = RichTextField(label='Usability questions and comments')
    usability.group = 3

    sustainability_rate = RequiredRateChoiceField(
        label='7. Sustainability',
        help_text='Is this proposal clearly located within a larger plan for future project support, development, and implementation? '
        'Does the project have a diversified funding/support stream i.e., how dependent would the project be on OTF? '
        'Is the proposing entity able to sustain itself with the requested OTF funding in addition to other sources of '
        'direct or indirect support, such as community or other in-kind support that it already receives? '
        'Does the proposal identify any cost sharing or matching support for the proposed effort? '
        'Does the project currently receive any U.S. government or other public funding?'
    )
    sustainability_rate.group = 3

    sustainability = RichTextField(label='Sustainability questions and comments')
    sustainability.group = 3

    collaboration_rate = RequiredRateChoiceField(
        label='8. Collaboration',
        help_text='Does the project support and further a collaborative and open community? '
        'Does the proposal facilitate inter-project collaboration, such as talking with like projects and '
        'identifying potential complementary aspects or points of overlap? '
        'Does the project seek to share resources or enable others to reuse the resources they develop? '
        'Do the objectives of this proposal contribute broadly to other Internet freedom projects?'
    )
    collaboration_rate.group = 3

    collaboration = RichTextField(label='Collaboration questions and comments')
    collaboration.group = 3

    realism_rate = RequiredRateChoiceField(
        label='9. Cost realism',
        help_text='Is the budget realistic and commensurate with both the project objectives and time frame? '
        'Is this project realistically implementable within a payment-on-delivery framework, i.e. no funds up-front?'
    )
    realism_rate.group = 3

    realism = RichTextField(label='Cost realism questions and comments')
    realism.group = 3

    qualifications_rate = RequiredRateChoiceField(
        label='10. Qualifications',
        help_text='Is the project team uniquely qualified to complete the proposed scope of work? '
        'Does the team have a history of successful work relevant to the proposed effort? '
        'Have team members worked with at-risk communities in the past? Does the proposing entity have a sufficient '
        'core team (leadership, developers, etc.) dedicated to this project? Are project team member(s) clearly '
        'identified, along with work experience, in the proposal?'
    )
    qualifications_rate.group = 3

    qualifications = RichTextField(label='Qualifications questions and comments')
    qualifications.group = 3

    evaluation_rate = RequiredRateChoiceField(
        label='11. Evaluation',
        help_text='Does the project articulate a clear set of evaluation criteria and milestone metrics against activities, objectives, and deliverables? '
        'Are the criteria and metrics measurable quantitatively and/or qualitatively? '
        'How difficult will an assessment of success or failure be? '
        'Does the proposing entity have the capacity to self-evaluate and extract “lessons learned”? '
        'Is the proposed effort able to be openly peer reviewed and/or include a peer review process?'
    )
    evaluation_rate.group = 3

    evaluation = RichTextField(label='Evaluation questions and comments')
    evaluation.group = 3

    # D. Rationale and appropriateness consideration
    rationale_rate = RateChoiceField(label='Rationale and appropriateness rating')
    rationale_rate.group = 4

    rationale = RichTextField(label='Rationale and appropriateness questions and comments')
    rationale.group = 4

    # E. General recommendation
    recommendation = forms.ChoiceField(choices=RECOMMENDATION_CHOICES, label='Recommendation')
    recommendation.group = 5

    recommendation_comments = RichTextField(label='Recommendation comments')
    recommendation_comments.group = 5
