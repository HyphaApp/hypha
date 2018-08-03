from django.urls import include, path

from .views import (
    RevisionCompareView,
    RevisionListView,
    SubmissionDetailView,
    SubmissionEditView,
    SubmissionListView,
    SubmissionSealedView,
    SubmissionSearchView,
)


revision_urls = ([
    path('', RevisionListView.as_view(), name='list'),
    path('compare/<int:to>/<int:from>', RevisionCompareView.as_view(), name='compare'),
], 'revisions')


app_name = 'funds'

submission_urls = ([
    path('', SubmissionListView.as_view(), name="list"),
    path('<int:pk>/', SubmissionDetailView.as_view(), name="detail"),
    path('<int:pk>/edit/', SubmissionEditView.as_view(), name="edit"),
    path('<int:pk>/sealed/', SubmissionSealedView.as_view(), name="sealed"),
    path('<int:submission_pk>/', include('opentech.apply.review.urls', namespace="reviews")),
    path('<int:submission_pk>/', include('opentech.apply.determinations.urls', namespace="determinations")),
    path('<int:submission_pk>/revisions/', include(revision_urls, namespace="revisions")),
], 'submissions')


urlpatterns = [
    path('submissions/', include(submission_urls)),
    path('search', SubmissionSearchView.as_view(), name="search"),
]
