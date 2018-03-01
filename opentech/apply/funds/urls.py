from django.urls import path

from .views import SubmissionSearchView, SubmissionDetailView, SubmissionListView, demo_workflow


app_name = 'funds'

urlpatterns = [
    path('demo/<int:wf_id>/', demo_workflow, name="workflow_demo"),
    path('submissions/', SubmissionListView.as_view(), name="submissions"),
    path('submissions/<int:pk>/', SubmissionDetailView.as_view(), name="submission"),
    path('search', SubmissionSearchView.as_view(), name="search"),
]
