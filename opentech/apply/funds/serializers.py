import collections

from rest_framework import serializers

from .models import ApplicationSubmission


class SubmissionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationSubmission
        fields = ('id', 'title', 'status')


class SubmissionDetailSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()
    meta_questions = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationSubmission
        fields = ('id', 'title', 'questions', 'meta_questions')

    def get_all_questions(self, obj, filter_func=None):
        for field_id in obj.question_field_ids:
            if filter_func is not None:
                if not filter_func(field_id):
                    continue
            field = obj.field(field_id)
            # TODO: Check field to see if answer can be serialized
            data = obj.data(field_id)

            yield {
                'id': field_id,
                'question': field.value['field_label'],
                'answer': data,
            }

    def get_meta_questions(self, obj):
        return self.get_all_questions(
            obj,
            filter_func=lambda field_id: field_id in obj.named_blocks
        )

    def get_questions(self, obj):
        return self.get_all_questions(
            obj,
            filter_func=lambda field_id: field_id not in obj.named_blocks
        )
