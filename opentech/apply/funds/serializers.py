from rest_framework import serializers
from wagtail.core.models import Page

from opentech.apply.activity.models import Activity
from .models import ApplicationSubmission


class ActionSerializer(serializers.Field):
    def to_representation(self, instance):
        actions = instance.get_actions_for_user(self.context['request'].user)
        return {
            transition: action
            for transition, action in actions
        }


class ReviewSummarySerializer(serializers.Field):
    def to_representation(self, instance):
        return {
            'count': instance.reviews.count(),
            'score': instance.reviews.score(),
            'recommendation': instance.reviews.recommendation(),
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

    class Meta:
        model = ApplicationSubmission
        fields = ('id', 'title', 'stage', 'status', 'meta_questions', 'questions', 'actions', 'review')

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
    actions = ActionSerializer(source='*')

    class Meta:
        model = ApplicationSubmission
        fields = ('id', 'actions',)


class RoundLabSerializer(serializers.ModelSerializer):
    workflow = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ('id', 'title', 'workflow')

    def __init__(self, *args, **kwargs):
        show_workflow = kwargs.pop('show_workflow', False)
        if not show_workflow:
            del self.fields['workflow']
        super().__init__(*args, **kwargs)

    def get_workflow(self, obj):
        return [
            {
                'value': phase.name,
                'display': phase.display_name
            }
            for phase in obj.workflow.values()
        ]


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Activity
        fields = ('id', 'timestamp', 'user', 'submission', 'message', 'visibility')


class CommentCreateSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Activity
        fields = ('id', 'timestamp', 'user', 'message', 'visibility')
