import json

from django import forms
from django.core.exceptions import NON_FIELD_ERRORS

from opentech.apply.review.blocks import ScoredAnswerField
from opentech.apply.review.options import NA

from .models import Review


class ReviewModelForm(forms.ModelForm):
    draft_button_name = "save_draft"

    class Meta:
        model = Review
        fields = ['recommendation', 'score', 'submission', 'author']

        widgets = {
            'recommendation': forms.HiddenInput(),
            'score': forms.HiddenInput(),
            'submission': forms.HiddenInput(),
            'author': forms.HiddenInput(),
        }

        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together': "You have already posted a review for this submission",
            }
        }

    def __init__(self, *args, user, submission, review_form, initial={}, instance=None, **kwargs):
        initial.update(submission=submission.id)
        initial.update(author=user.id)

        if instance:
            for key, value in instance.form_data.items():
                if key not in self._meta.fields:
                    initial[key] = value

        super().__init__(*args, initial=initial, instance=instance, **kwargs)
        self.review_form = review_form
        self.form_fields = review_form.get_form_fields()

        for name, field in self.form_fields.items():
            self.fields.update({name: field})

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
        self.instance.score = self.calculate_score()
        self.instance.recommendation = self.cleaned_data[self.review_form.get_recommendation_field()]
        self.instance.is_draft = self.draft_button_name in self.data
        self.instance.form_data = self.cleaned_data['form_data']
        self.instance.form_fields = self.review_form.get_defined_fields()

        return super().save(commit)

    def calculate_score(self):
        scores = list()

        for field in self.get_score_fields():
            value = json.loads(self.cleaned_data.get(field, '[null, null]'))

            try:
                score = int(value[1])
                if score != NA:
                    scores.append(score)
            except TypeError:
                pass

        try:
            return sum(scores) / len(scores)
        except ZeroDivisionError:
            return 0

    def get_score_fields(self):
        return [field_name for field_name, field in self.fields.items() if isinstance(field, ScoredAnswerField)]
