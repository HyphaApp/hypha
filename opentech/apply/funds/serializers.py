import mistune

from django.contrib.auth import get_user_model

from django_bleach.templatetags.bleach_tags import bleach_value
from rest_framework import serializers

from opentech.apply.activity.models import Activity
from opentech.apply.determinations.views import DeterminationCreateOrUpdateView
from opentech.apply.review.models import Review, ReviewOpinion
from opentech.apply.review.options import RECOMMENDATION_CHOICES
from opentech.apply.users.groups import PARTNER_GROUP_NAME, STAFF_GROUP_NAME
from .models import ApplicationSubmission, RoundsAndLabs

User = get_user_model()

markdown = mistune.Markdown()


class ActionSerializer(serializers.Field):
    def to_representation(self, instance):
        actions = instance.get_actions_for_user(self.context['request'].user)
        representation = []
        for transition, action in actions:
            action_dict = {
                'value': transition,
                'display': action
            }

            # Sometimes the status does not exist in the
            # determination matrix.
            try:
                redirect = DeterminationCreateOrUpdateView.should_redirect(
                    None,
                    instance,
                    transition,
                )
            except KeyError:
                redirect = None
            if redirect:
                action_dict['type'] = 'redirect'
                action_dict['target'] = redirect.url
            else:
                action_dict['type'] = 'submit'

            representation.append(action_dict)
        return representation


class OpinionSerializer(serializers.ModelSerializer):
    author_id = serializers.ReadOnlyField(source='author.id')
    opinion = serializers.ReadOnlyField(source='get_opinion_display')

    class Meta:
        model = ReviewOpinion
        fields = ('author_id', 'opinion')


class ReviewSerializer(serializers.ModelSerializer):
    author_id = serializers.ReadOnlyField(source='author.id')
    url = serializers.ReadOnlyField(source='get_absolute_url')
    opinions = OpinionSerializer(read_only=True, many=True)
    recommendation = serializers.SerializerMethodField()
    score = serializers.ReadOnlyField(source='get_score_display')

    class Meta:
        model = Review
        fields = ('id', 'score', 'author_id', 'url', 'opinions', 'recommendation')

    def get_recommendation(self, obj):
        return {
            'value': obj.recommendation,
            'display': obj.get_recommendation_display(),
        }


class ReviewSummarySerializer(serializers.Serializer):
    reviews = ReviewSerializer(many=True, read_only=True)
    count = serializers.ReadOnlyField(source='reviews.count')
    score = serializers.ReadOnlyField(source='reviews.score')
    recommendation = serializers.SerializerMethodField()
    assigned = serializers.SerializerMethodField()

    def get_recommendation(self, obj):
        recommendation = obj.reviews.recommendation()
        return {
            'value': recommendation,
            'display': dict(RECOMMENDATION_CHOICES).get(recommendation),
        }

    def get_assigned(self, obj):
        assigned_reviewers = obj.assigned.select_related('reviewer', 'role', 'type')
        response = [
            {
                'id': assigned.id,
                'name': str(assigned.reviewer),
                'role': {
                    'icon': assigned.role and assigned.role.icon_url('fill-12x12'),
                    'name': assigned.role and assigned.role.name,
                    'order': assigned.role and assigned.role.order,
                },
                'is_staff': assigned.type.name == STAFF_GROUP_NAME,
                'is_partner': assigned.type.name == PARTNER_GROUP_NAME,
            } for assigned in assigned_reviewers
        ]
        return response


class TimestampField(serializers.Field):
    def to_representation(self, value):
        return value.timestamp() * 1000


class SubmissionListSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='funds:api:submissions:detail')
    round = serializers.SerializerMethodField()
    last_update = TimestampField()

    class Meta:
        model = ApplicationSubmission
        fields = ('id', 'title', 'status', 'url', 'round', 'last_update')

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
    screening = serializers.ReadOnlyField(source='screening_status.title')

    class Meta:
        model = ApplicationSubmission
        fields = ('id', 'title', 'stage', 'status', 'phase', 'meta_questions', 'questions', 'actions', 'review', 'screening')

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

    class Meta:
        model = ApplicationSubmission
        fields = ('id', 'actions')


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
    edit_url = serializers.HyperlinkedIdentityField(view_name='funds:api:comments:edit')
    editable = serializers.SerializerMethodField()
    timestamp = TimestampField(read_only=True)
    edited = TimestampField(read_only=True)

    class Meta:
        model = Activity
        fields = ('id', 'timestamp', 'user', 'source', 'message', 'visibility', 'edited', 'edit_url', 'editable')

    def get_message(self, obj):
        return bleach_value(markdown(obj.message))

    def get_editable(self, obj):
        return self.context['request'].user == obj.user


class CommentCreateSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    edit_url = serializers.HyperlinkedIdentityField(view_name='funds:api:comments:edit')
    editable = serializers.SerializerMethodField()
    timestamp = TimestampField(read_only=True)
    edited = TimestampField(read_only=True)

    class Meta:
        model = Activity
        fields = ('id', 'timestamp', 'user', 'message', 'visibility', 'edited', 'edit_url', 'editable')

    def get_editable(self, obj):
        return self.context['request'].user == obj.user


class CommentEditSerializer(CommentCreateSerializer):
    class Meta(CommentCreateSerializer.Meta):
        read_only_fields = ('timestamp', 'visibility', 'edited',)
