import json

from django import forms
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS

from .models import Review, RECOMMENDATION_CHOICES


RATE_CHOICES = (
    (0, '0. Need more info'),
    (1, '1. Poor'),
    (2, '2. Not so good'),
    (3, '3. Is o.k.'),
    (4, '4. Good'),
    (5, '5. Excellent'),
    (99, 'n/a - choose not to answer'),
)


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
        super().validate_unique()

        self.instance.submission = self.submission
        self.instance.author = self.request.user
        self.instance.review = json.dumps(self.cleaned_data)

        try:
            self.instance.validate_unique()
        except ValidationError as e:
            self._update_errors(e)


class ConceptReviewForm(BaseReviewForm):
    recommendation = forms.ChoiceField(
        choices=RECOMMENDATION_CHOICES,
        label='Overall recommendation',
        help_text='Do you recommend requesting a proposal based on this concept note?'
    )
    recommendation_comments = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5}),
        label='Recommendation comments'
    )
    principles = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5}),
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

    principles_rate = forms.ChoiceField(
        choices=RATE_CHOICES,
        label='Rate goals and principles'
    )

    technical = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5}),
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
    technical_rate = forms.ChoiceField(
        choices=RATE_CHOICES,
        label='Rate technical merit'
    )

    sustainable = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5}),
        label='Reasonable and realistic',
        help_text='Is the requested amount reasonable, realistic, and justified? Does the project provide a detailed '
        'and realistic description of effort and schedule? I.e. is the project capable of creating a work plan '
        'including objectives, activities, and deliverable(s)?'
    )
    sustainable_rate = forms.ChoiceField(
        choices=RATE_CHOICES,
        label='Rate reasonable and realisti'
    )

    comments = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5}),
        label='General comments'
    )

    request_questions = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5}),
        label='Request specific questions'
    )


class ProposalReviewForm(BaseReviewForm):
    pass
