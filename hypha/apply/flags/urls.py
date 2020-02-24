from django.urls import path

from .views import FlagSubmissionCreateView

app_name = 'flags'

urlpatterns = [
    path('<int:submission_pk>/<type>/flag/', FlagSubmissionCreateView.as_view(), name="create_submission_flag"),
]
