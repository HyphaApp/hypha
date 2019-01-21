from django.urls import include, path

from .views import (
    RevisionCompareView,
    RevisionListView,
    RoundListView,
    SubmissionsByRound,
    SubmissionDetailView,
    SubmissionEditView,
    SubmissionListView,
    SubmissionListAllView,
    SubmissionSealedView,
)
from .api_views import SubmissionList, SubmissionDetail


revision_urls = ([
    path('', RevisionListView.as_view(), name='list'),
    path('compare/<int:to>/<int:from>/', RevisionCompareView.as_view(), name='compare'),
], 'revisions')


app_name = 'funds'

submission_urls = ([
    path('', SubmissionListView.as_view(), name="list"),
    path('all/', SubmissionListAllView.as_view(), name="list"),
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
], 'submissions')


submission_api_urls = ([
    path('', SubmissionList.as_view(), name='list'),
    path('<int:pk>/', SubmissionDetail.as_view(), name='detail'),
], 'submissions-api')


rounds_urls = ([
    path('', RoundListView.as_view(), name="list"),
    path('<int:pk>/', SubmissionsByRound.as_view(), name="detail"),
], 'rounds')


urlpatterns = [
    path('submissions/', include(submission_urls)),
    path('rounds/', include(rounds_urls)),
    path('api/submissions/', include(submission_api_urls)),
]
