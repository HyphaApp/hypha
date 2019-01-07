from django.urls import include, path

from .views import (
    RevisionCompareView,
    RevisionListView,
    SubmissionsByRound,
    SubmissionDetailView,
    SubmissionEditView,
    SubmissionListView,
    SubmissionSealedView,
    SubmissionSearchView,
)


revision_urls = ([
    path('', RevisionListView.as_view(), name='list'),
    path('compare/<int:to>/<int:from>/', RevisionCompareView.as_view(), name='compare'),
], 'revisions')


app_name = 'funds'

submission_urls = ([
    path('', SubmissionListView.as_view(), name="list"),
    path('<int:pk>/', include([
        path('', SubmissionDetailView.as_view(), name="detail"),
        path('edit/', SubmissionEditView.as_view(), name="edit"),
        path('sealed/', SubmissionSealedView.as_view(), name="sealed"),
    ])),
    path('<int:submission_pk>/', include([
        path('', include('opentech.apply.review.urls', namespace="reviews")),
        path('', include('opentech.apply.determinations.urls', namespace="determinations")),
        path('revisions/', include(revision_urls, namespace="revisions")),
    ])),
    path('rounds/<int:pk>/', SubmissionsByRound.as_view(), name="by_round"),
], 'submissions')


urlpatterns = [
    path('submissions/', include(submission_urls)),
    path('search/', SubmissionSearchView.as_view(), name="search"),
]
