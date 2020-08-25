from collections import OrderedDict

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from hypha.apply.review.options import RATE_CHOICES


class ScoredAnswerListField(serializers.ListField):
    childs = [
        serializers.CharField(),
        serializers.ChoiceField(choices=RATE_CHOICES)
    ]

    def run_child_validation(self, data):
        result = []
        errors = OrderedDict()

        for idx, item in enumerate(data):
            try:
                result.append(self.childs[idx].run_validation(item))
            except ValidationError as e:
                errors[idx] = e.detail

        if not errors:
            return result
        raise ValidationError(errors)
