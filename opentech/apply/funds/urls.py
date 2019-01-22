from django.urls import include, path

from .views import (
    RevisionCompareView,
    RevisionListView,
    RoundListView,
    SubmissionsByRound,
    SubmissionDetailView,
    SubmissionEditView,
    SubmissionListView,
    SubmissionSealedView,
)
from .api_views import (
    CommentList,
    CommentListCreate,
    RoundLabDetail,
    SubmissionAction,
    SubmissionList,
    SubmissionDetail,
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
], 'submissions')

api_urls = ([
    path('submissions/', include(([
        path('', SubmissionList.as_view(), name='list'),
        path('<int:pk>/', SubmissionDetail.as_view(), name='detail'),
        path('<int:pk>/actions/', SubmissionAction.as_view(), name='actions'),
        path('<int:pk>/comments/', CommentListCreate.as_view(), name='comments'),
    ], 'submissions'))),
    path('rounds/', include(([
        path('<int:pk>/', RoundLabDetail.as_view(), name='detail'),
    ], 'rounds'))),
    path('comments/', include(([
        path('', CommentList.as_view(), name='list'),
    ], 'comments')))
], 'api')

rounds_urls = ([
    path('', RoundListView.as_view(), name="list"),
    path('<int:pk>/', SubmissionsByRound.as_view(), name="detail"),
], 'rounds')


urlpatterns = [
    path('submissions/', include(submission_urls)),
    path('rounds/', include(rounds_urls)),
    path('api/', include(api_urls)),
]
