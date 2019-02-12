import mistune
from rest_framework import serializers
from django_bleach.templatetags.bleach_tags import bleach_value

from opentech.apply.activity.models import Activity
from opentech.apply.review.options import RECOMMENDATION_CHOICES
from .models import ApplicationSubmission, RoundsAndLabs

markdown = mistune.Markdown()


class ActionSerializer(serializers.Field):
    def to_representation(self, instance):
        actions = instance.get_actions_for_user(self.context['request'].user)
        return [
            {'value': transition, 'display': action}
            for transition, action in actions
        ]


class ReviewSummarySerializer(serializers.Field):
    def to_representation(self, instance):
        reviews = instance.reviews.select_related('author')
        recommendation = reviews.recommendation()

        return {
            'count': len(reviews),
            'score': reviews.score(),
            'recommendation': {
                'value': recommendation,
                'display': dict(RECOMMENDATION_CHOICES).get(recommendation)
            },
            'reviews': [
                {
                    'id': review.id,
                    'author': str(review.author),
                    'score': review.score,
                    'recommendation': {
                        'value': review.recommendation,
                        'display': review.get_recommendation_display(),
                    },
                    'review_url': review.get_absolute_url(),
                } for review in reviews
            ]
        }


class SubmissionListSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='funds:api:submissions:detail')
    round = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationSubmission
        fields = ('id', 'title', 'status', 'url', 'round')

    def get_round(self, obj):
        """
        This gets round or lab ID.
        """
        return obj.round_id or obj.page_id


class SubmissionDetailSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()
    meta_questions = serializers.SerializerMethodField()
    stage = serializers.CharField(source='stage.name')
    actions = ActionSerializer(source='*')
    review = ReviewSummarySerializer(source='*')
    phase = serializers.CharField()

    class Meta:
        model = ApplicationSubmission
        fields = ('id', 'title', 'stage', 'status', 'phase', 'meta_questions', 'questions', 'actions', 'review')

    def serialize_questions(self, obj, fields):
        for field_id in fields:
            yield obj.serialize(field_id)

    def get_meta_questions(self, obj):
        meta_questions = {
            'title': 'Project Name',
            'full_name': 'Legal Name',
            'email': 'Email',
            'value': 'Requested Funding',
            'duration': 'Project Duration',
            'address': 'Address'
        }
        data = self.serialize_questions(obj, obj.named_blocks.values())
        data = [
            {
                **response,
                'question': meta_questions.get(response['type'], response['question'])
            }
            for response in data
        ]
        return data

    def get_questions(self, obj):
        return self.serialize_questions(obj, obj.normal_blocks)


class SubmissionActionSerializer(serializers.ModelSerializer):
    actions = ActionSerializer(source='*', read_only=True)
    action = serializers.CharField(write_only=True)

    class Meta:
        model = ApplicationSubmission
        fields = ('id', 'actions', 'action')


class RoundLabDetailSerializer(serializers.ModelSerializer):
    workflow = serializers.SerializerMethodField()

    class Meta:
        model = RoundsAndLabs
        fields = ('id', 'title', 'workflow')

    def get_workflow(self, obj):
        return [
            {
                'value': phase.name,
                'display': phase.display_name
            }
            for phase in obj.workflow.values()
        ]


class RoundLabSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoundsAndLabs
        fields = ('id', 'title')


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    message = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = ('id', 'timestamp', 'user', 'submission', 'message', 'visibility')

    def get_message(self, obj):
        return bleach_value(markdown(obj.message))


class CommentCreateSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Activity
        fields = ('id', 'timestamp', 'user', 'message', 'visibility')
