from django.urls import include, path

from .views import SubmissionSearchView, SubmissionDetailView, SubmissionEditView, SubmissionListView


app_name = 'funds'

urlpatterns = [
    path('submissions/', SubmissionListView.as_view(), name="submissions"),
    path('submissions/<int:pk>/', SubmissionDetailView.as_view(), name="submission"),
    path('submissions/<int:pk>/edit', SubmissionEditView.as_view(), name="edit_submission"),
    path('submissions/<int:submission_pk>/', include('opentech.apply.review.urls', namespace="reviews")),
    path('search', SubmissionSearchView.as_view(), name="search"),
]
