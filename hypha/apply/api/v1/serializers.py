import mistune
from django.contrib.auth import get_user_model
from django_bleach.templatetags.bleach_tags import bleach_value
from rest_framework import serializers

from hypha.apply.activity.models import Activity
from hypha.apply.categories.models import MetaTerm
from hypha.apply.determinations.models import Determination
from hypha.apply.determinations.templatetags.determination_tags import (
    show_determination_button,
)
from hypha.apply.determinations.views import DeterminationCreateOrUpdateView
from hypha.apply.funds.models import (
    ApplicationSubmission,
    RoundsAndLabs,
    ScreeningStatus,
)
from hypha.apply.review.models import Review, ReviewOpinion
from hypha.apply.review.options import RECOMMENDATION_CHOICES
from hypha.apply.users.groups import PARTNER_GROUP_NAME, STAFF_GROUP_NAME

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
    user_id = serializers.SerializerMethodField()
    author_id = serializers.ReadOnlyField(source='author.id')
    url = serializers.ReadOnlyField(source='get_absolute_url')
    opinions = OpinionSerializer(read_only=True, many=True)
    recommendation = serializers.SerializerMethodField()
    score = serializers.ReadOnlyField(source='get_score_display')

    class Meta:
        model = Review
        fields = ('id', 'score', 'user_id', 'author_id', 'url', 'opinions', 'recommendation')

    def get_recommendation(self, obj):
        return {
            'value': obj.recommendation,
            'display': obj.get_recommendation_display(),
        }

    def get_user_id(self, obj):
        return obj.author.reviewer.id


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


class DeterminationSerializer(serializers.ModelSerializer):
    outcome = serializers.ReadOnlyField(source='get_outcome_display')
    author = serializers.CharField(read_only=True)
    url = serializers.ReadOnlyField(source='get_absolute_url')
    updated_at = serializers.DateTimeField(read_only=True)
    is_draft = serializers.BooleanField(read_only=True)

    class Meta:
        model = Determination
        fields = ('id', 'outcome', 'author', 'url', 'updated_at', 'is_draft')


class DeterminationSummarySerializer(serializers.Serializer):
    determinations = DeterminationSerializer(many=True, read_only=True)
    count = serializers.ReadOnlyField(source='determinations.count')


class SubmissionListSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='api:v1:submissions-detail')
    round = serializers.SerializerMethodField()
    last_update = TimestampField()

    class Meta:
        model = ApplicationSubmission
        fields = ('id', 'title', 'status', 'url', 'round', 'last_update', 'summary')

    def get_round(self, obj):
        """
        This gets round or lab ID.
        """
        return obj.round_id or obj.page_id


class MetaTermsDetailSerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField()

    class Meta:
        model = MetaTerm
        fields = ("id", "name", "parent")

    def get_parent(self, obj):
        parent = obj.get_parent()
        if parent:
            parent_data = {
                'id': parent.id,
                'name': parent.name
            }
            return parent_data


class SubmissionSummarySerializer(serializers.Serializer):
    summary = serializers.CharField(write_only=True)


class SubmissionMetaTermsSerializer(serializers.Serializer):
    meta_terms = serializers.PrimaryKeyRelatedField(many=True, queryset=MetaTerm.objects.all())


class SubmissionDetailSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()
    meta_questions = serializers.SerializerMethodField()
    meta_terms = MetaTermsDetailSerializer(many=True)
    stage = serializers.CharField(source='stage.name')
    actions = ActionSerializer(source='*')
    review = ReviewSummarySerializer(source='*')
    determination = DeterminationSummarySerializer(source='*')
    phase = serializers.CharField()
    screening = serializers.SerializerMethodField()
    action_buttons = serializers.SerializerMethodField()
    is_determination_form_attached = serializers.BooleanField(read_only=True)
    is_user_staff = serializers.SerializerMethodField()
    flags = serializers.SerializerMethodField()
    reminders = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationSubmission
        fields = ('id', 'summary', 'title', 'stage', 'status', 'phase', 'meta_questions', 'meta_terms', 'questions', 'actions', 'review', 'screening', 'action_buttons', 'determination', 'is_determination_form_attached', 'is_user_staff', 'screening', 'flags', 'reminders')

    def serialize_questions(self, obj, fields):
        for field_id in fields:
            yield obj.serialize(field_id)

    def get_is_user_staff(self, obj):
        request = self.context['request']
        return request.user.is_apply_staff

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

    def get_screening(self, obj):
        selected_default = {}
        selected_reasons = []
        all_screening = []

        for screening in obj.screening_statuses.values():
            if screening['default']:
                selected_default = screening
            else:
                selected_reasons.append(screening)

        for screening in ScreeningStatus.objects.values():
            all_screening.append(screening)

        screening = {
            "selected_reasons": selected_reasons,
            "selected_default": selected_default,
            "all_screening": all_screening
        }
        return screening

    def get_flags(self, obj):
        flags = [
            {
                "type": 'user',
                "selected": obj.flagged_by(self.context['request'].user)
            },
            {
                "type": 'staff',
                "selected": obj.flagged_staff
            }
        ]

        return flags

    def get_questions(self, obj):
        return self.serialize_questions(obj, obj.normal_blocks)

    def get_reminders(self, obj):
        reminders = []
        for reminder in obj.reminders.all():
            reminders.append({
                "id": reminder.id,
                "submission_id": reminder.submission_id,
                "title": reminder.title,
                "action_type": reminder.action_type,
                "is_expired": reminder.is_expired
            })
        return reminders

    def get_action_buttons(self, obj):
        request = self.context['request']
        add_review = (
            obj.phase.permissions.can_review(request.user) and
            obj.can_review(request.user) and not
            obj.assigned.draft_reviewed().filter(reviewer=request.user).exists()
        )
        show_determination = (
            show_determination_button(request.user, obj)
        )
        return {
            'add_review': add_review,
            'show_determination_button': show_determination,
        }


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


class OpenRoundLabSerializer(serializers.ModelSerializer):
    start_date = serializers.DateField(read_only=True)
    end_date = serializers.DateField(read_only=True)

    class Meta:
        model = RoundsAndLabs
        fields = ('id', 'title', 'url_path', 'search_description', 'start_date', 'end_date')


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    message = serializers.SerializerMethodField()
    edit_url = serializers.HyperlinkedIdentityField(view_name='api:v1:comments-edit')
    editable = serializers.SerializerMethodField()
    timestamp = TimestampField(read_only=True)
    edited = TimestampField(read_only=True)

    class Meta:
        model = Activity
        fields = ('id', 'timestamp', 'user', 'message', 'visibility', 'edited', 'edit_url', 'editable')

    def get_message(self, obj):
        return bleach_value(markdown(obj.message))

    def get_editable(self, obj):
        return self.context['request'].user == obj.user


class CommentCreateSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    edit_url = serializers.HyperlinkedIdentityField(view_name='api:v1:comments-edit')
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
        read_only_fields = ('timestamp', 'edited',)


class UserSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    email = serializers.CharField(read_only=True)


class MetaTermsSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField(
        read_only=True, method_name="get_children_nodes"
    )

    class Meta:
        model = MetaTerm
        fields = ("name", "id", "children")

    def get_children_nodes(self, obj):
        child_queryset = obj.get_children()
        return MetaTermsSerializer(child_queryset, many=True).data
