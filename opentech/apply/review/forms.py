from django import forms
from django.core.exceptions import NON_FIELD_ERRORS
from django.utils.html import escape

from opentech.apply.review.options import NA
from opentech.apply.stream_forms.forms import StreamBaseForm

from .models import Review, ReviewOpinion
from .options import OPINION_CHOICES, PRIVATE


class MixedMetaClass(type(StreamBaseForm), type(forms.ModelForm)):
    pass


class ReviewModelForm(StreamBaseForm, forms.ModelForm, metaclass=MixedMetaClass):
    draft_button_name = "save_draft"

    class Meta:
        model = Review
        fields = ['recommendation', 'visibility', 'score', 'submission']

        widgets = {
            'recommendation': forms.HiddenInput(),
            'score': forms.HiddenInput(),
            'submission': forms.HiddenInput(),
            'visibility': forms.HiddenInput(),
        }

        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together': "You have already posted a review for this submission",
            }
        }

    def __init__(self, *args, submission, user=None, initial={}, instance=None, **kwargs):
        initial.update(submission=submission.id)

        if instance:
            for key, value in instance.form_data.items():
                if key not in self._meta.fields:
                    initial[key] = value

        super().__init__(*args, initial=initial, instance=instance, **kwargs)

        for field in self._meta.widgets:
            self.fields[field].disabled = True

        if self.draft_button_name in self.data:
            for field in self.fields.values():
                field.required = False

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['form_data'] = {
            key: value
            for key, value in cleaned_data.items()
            if key not in self._meta.fields
        }

        return cleaned_data

    def save(self, commit=True):
        self.instance.score = self.calculate_score(self.cleaned_data)
        self.instance.recommendation = int(self.cleaned_data[self.instance.recommendation_field.id])
        self.instance.is_draft = self.draft_button_name in self.data
        # Old review forms do not have the requred visability field.
        # This will set visibility to PRIVATE by default.
        try:
            self.instance.visibility = self.cleaned_data[self.instance.visibility_field.id]
        except AttributeError:
            self.instance.visibility = PRIVATE

        self.instance.form_data = self.cleaned_data['form_data']

        if not self.instance.is_draft:
            # Capture the revision against which the user was reviewing
            self.instance.revision = self.instance.submission.live_revision

        return super().save(commit)

    def calculate_score(self, data):
        scores = list()

        for field in self.instance.score_fields:
            score = data.get(field.id)[1]
            # Include NA answers as 0.
            if score == NA:
                score = 0
            scores.append(score)

        try:
            return sum(scores) / len(scores)
        except ZeroDivisionError:
            return NA


class SubmitButtonWidget(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        disabled = 'disabled' if attrs.get('disabled') else ''
        return '<input type="submit" name="{name}" value="{value}" class="button button--primary button--bottom-space" {disabled}>'.format(
            disabled=disabled,
            name=escape(name),
            value=escape(name.title()),
        )


class OpinionField(forms.IntegerField):
    def __init__(self, *args, opinion, **kwargs):
        kwargs["widget"] = SubmitButtonWidget
        self.opinion = opinion
        kwargs['label'] = ''
        super().__init__(*args, **kwargs)

    def clean(self, value):
        if value:
            return self.opinion


class ReviewOpinionForm(forms.ModelForm):
    opinion = forms.IntegerField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = ReviewOpinion
        fields = ('opinion',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for value, opinion in OPINION_CHOICES:
            self.fields[opinion.lower()] = OpinionField(
                label=opinion.title(),
                opinion=value,
                disabled=self.instance.opinion == value,
            )

    def clean(self):
        cleaned_data = super().clean()
        opinions = [cleaned_data.get(opinion.lower()) for _, opinion in OPINION_CHOICES]
        valid_opinions = [opinion for opinion in opinions if opinion is not None]
        if len(valid_opinions) > 1:
            self.add_error(None, 'Cant submit both an agreement and disagreement')
        cleaned_data = {'opinion': valid_opinions[0]}
        return cleaned_data

    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)
