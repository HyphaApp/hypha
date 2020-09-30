from rest_framework import serializers

from hypha.apply.review.models import Review, ReviewOpinion
from hypha.apply.review.options import NA, NO, PRIVATE
from hypha.apply.stream_forms.forms import BlockFieldWrapper

from ..utils import get_field_kwargs, get_field_widget


class ReviewOpinionReadSerializer(serializers.ModelSerializer):
    author_id = serializers.ReadOnlyField(source='author.id')
    opinion = serializers.ReadOnlyField(source='get_opinion_display')

    class Meta:
        model = ReviewOpinion
        fields = ('author_id', 'opinion')


class ReviewOpinionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewOpinion
        fields = ('opinion', )
        extra_kwargs = {'opinion': {'write_only': True}}


class SubmissionReviewDetailSerializer(serializers.ModelSerializer):
    """
    TODO

    Remove this serializer if not in used.
    """
    author_id = serializers.ReadOnlyField(source='author.id')
    opinions = ReviewOpinionReadSerializer(read_only=True, many=True)
    recommendation = serializers.SerializerMethodField()
    score = serializers.ReadOnlyField(source='get_score_display')
    questions = serializers.SerializerMethodField()
    comments = serializers.CharField(source='get_comments_display')

    class Meta:
        model = Review
        fields = [
            'id', 'score', 'author_id',
            'opinions', 'recommendation',
            'questions', 'comments', 'visibility'
        ]

    def get_recommendation(self, obj):
        return {
            'value': obj.recommendation,
            'display': obj.get_recommendation_display(),
        }

    def serialize_questions(self, obj, fields):
        for field_id in fields:
            yield obj.serialize(field_id)

    def get_questions(self, obj):
        return self.serialize_questions(obj, obj.normal_blocks)


class SubmissionReviewSerializer(serializers.ModelSerializer):
    opinions = ReviewOpinionReadSerializer(read_only=True, many=True)

    class Meta:
        model = Review
        fields = ['id', 'score', 'is_draft', 'opinions', ]
        extra_kwargs = {
            'score': {'read_only': True},
            'is_draft': {'required': False}
        }

    def get_recommendation(self, obj):
        return {
            'value': obj.recommendation,
            'display': obj.get_recommendation_display(),
        }

    def validate(self, data):
        validated_data = super().validate(data)
        validated_data['form_data'] = {
            key: value
            for key, value in validated_data.items()
        }
        return validated_data

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.score = self.calculate_score(instance, self.validated_data)
        recommendation = self.validated_data.get(instance.recommendation_field.id, NO)
        instance.recommendation = int(
            recommendation if recommendation is not None else NO
        )
        instance.is_draft = self.validated_data.get('is_draft', False)

        # Old review forms do not have the requred visability field.
        # This will set visibility to PRIVATE by default.
        try:
            instance.visibility = self.validated_data[instance.visibility_field.id]
        except AttributeError:
            instance.visibility = PRIVATE

        if not instance.is_draft:
            # Capture the revision against which the user was reviewing
            instance.revision = instance.submission.live_revision

        instance.save()
        return instance

    def calculate_score(self, instance, data):
        scores = list()
        for field in instance.score_fields:
            score = data.get(field.id, ['', NA])
            # Include NA answers as 0.
            score = score[1] if score is not None else NA
            if score == NA:
                score = 0
            scores.append(score)
        # Check if there are score_fields_without_text and also
        # append scores from them.
        for field in instance.score_fields_without_text:
            score = data.get(field.id, '')
            # Include '' answers as 0.
            if score is None or score == '':
                score = 0
            scores.append(int(score))

        try:
            return sum(scores) / len(scores)
        except ZeroDivisionError:
            return NA


class FieldSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    kwargs = serializers.SerializerMethodField()
    widget = serializers.SerializerMethodField()

    def get_id(self, obj):
        return obj[0]

    def get_type(self, obj):
        if isinstance(obj[1], BlockFieldWrapper):
            return 'LoadHTML'
        return obj[1].__class__.__name__

    def get_kwargs(self, obj):
        return get_field_kwargs(obj[1])

    def get_widget(self, obj):
        return get_field_widget(obj[1])
