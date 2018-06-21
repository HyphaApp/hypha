from django.urls import include, path

from .views import SubmissionSearchView, SubmissionDetailView, SubmissionEditView, SubmissionListView


app_name = 'funds'

submission_urls = ([
    path('', SubmissionListView.as_view(), name="list"),
    path('<int:pk>/', SubmissionDetailView.as_view(), name="detail"),
    path('<int:pk>/edit/', SubmissionEditView.as_view(), name="edit"),
    path('<int:submission_pk>/', include('opentech.apply.review.urls', namespace="reviews")),
    path('<int:submission_pk>/', include('opentech.apply.determinations.urls', namespace="determinations")),
], 'submissions')

urlpatterns = [
    path('submissions/', include(submission_urls)),
    path('search', SubmissionSearchView.as_view(), name="search"),
]
