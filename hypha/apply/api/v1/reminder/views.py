from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from hypha.apply.funds.models import Reminder

from ..mixin import SubmissionNestedMixin
from ..permissions import IsApplyStaffUser
from .serializers import SubmissionReminderSerializer


class SubmissionReminderViewSet(
    SubmissionNestedMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (
        permissions.IsAuthenticated,
        IsApplyStaffUser,
    )
    serializer_class = SubmissionReminderSerializer
    pagination_class = None

    def get_queryset(self):
        submission = self.get_submission_object()
        return Reminder.objects.filter(submission=submission).order_by("-time")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, submission=self.get_submission_object())

    def destroy(self, request, *args, **kwargs):
        reminder = self.get_object()
        reminder.delete()
        ser = self.get_serializer(self.get_queryset(), many=True)
        return Response(ser.data)

    @action(detail=False, methods=["get"])
    def fields(self, request, *args, **kwargs):
        """
        List details of all the form fields that were created by admin for adding reminders.

        These field details will be used in frontend to render the reminder form.
        """
        fields = [
            {
                "id": "title",
                "kwargs": {"required": True, "label": "Title", "max_length": 60},
                "type": "TextInput",
            },
            {
                "id": "description",
                "type": "textArea",
                "kwargs": {"label": "Description"},
                "widget": {"attrs": {"cols": 40, "rows": 5}, "type": "Textarea"},
            },
            {
                "id": "time",
                "kwargs": {"label": "Time", "required": True},
                "type": "DateTime",
            },
            {
                "id": "action",
                "kwargs": {
                    "label": "Action",
                    "required": True,
                    "choices": Reminder.ACTIONS.items(),
                    "initial": Reminder.REVIEW,
                },
                "type": "Select",
            },
        ]
        return Response(fields)
