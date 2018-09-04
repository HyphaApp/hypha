from django import forms
from django.core.exceptions import NON_FIELD_ERRORS

from opentech.apply.review.options import NA
from opentech.apply.stream_forms.forms import StreamBaseForm

from .models import Review


class MixedMetaClass(type(StreamBaseForm), type(forms.ModelForm)):
    pass


class ReviewModelForm(StreamBaseForm, forms.ModelForm, metaclass=MixedMetaClass):
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

    def __init__(self, *args, user, submission, initial={}, instance=None, **kwargs):
        initial.update(submission=submission.id)
        initial.update(author=user.id)

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

        self.instance.form_data = self.cleaned_data['form_data']

        if not self.instance.is_draft:
            # Capture the revision against which the user was reviewing
            self.instance.revision = self.instance.submission.live_revision

        return super().save(commit)

    def calculate_score(self, data):
        scores = list()

        for field in self.instance.score_fields:
            score = data.get(field.id)[1]
            if score != NA:
                scores.append(score)

        try:
            return sum(scores) / len(scores)
        except ZeroDivisionError:
            return NA
