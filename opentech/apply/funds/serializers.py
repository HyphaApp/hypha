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
        fields = ('id', 'title', 'meta_questions', 'questions')

    def serialize_questions(self, obj, fields):
        for field_id in fields:
            yield obj.serialize(field_id)

    def get_meta_questions(self, obj):
        return self.serialize_questions(obj, obj.named_blocks.values())

    def get_questions(self, obj):
        return self.serialize_questions(obj, obj.normal_blocks)
