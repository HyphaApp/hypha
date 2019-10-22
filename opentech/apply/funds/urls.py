from django.urls import include, path

from opentech.apply.projects import urls as projects_urls

from .views import (
    RevisionCompareView,
    RevisionListView,
    RoundListView,
    SubmissionsByRound,
    SubmissionsByStatus,
    SubmissionDetailView,
    SubmissionEditView,
    SubmissionListView,
    SubmissionOverviewView,
    SubmissionSealedView,
    SubmissionDeleteView,
    SubmissionPrivateMediaView,
    SubmissionDetailSimplifiedView
)


revision_urls = ([
    path('', RevisionListView.as_view(), name='list'),
    path('compare/<int:to>/<int:from>/', RevisionCompareView.as_view(), name='compare'),
], 'revisions')


app_name = 'funds'

submission_urls = ([
    path('', SubmissionOverviewView.as_view(), name="overview"),
    path('all/', SubmissionListView.as_view(), name="list"),
    path('<int:pk>/', include([
        path('', SubmissionDetailView.as_view(), name="detail"),
        path('edit/', SubmissionEditView.as_view(), name="edit"),
        path('sealed/', SubmissionSealedView.as_view(), name="sealed"),
        path('simplified/', SubmissionDetailSimplifiedView.as_view(), name="simplified"),
        path('delete/', SubmissionDeleteView.as_view(), name="delete"),
        path(
            'documents/<uuid:field_id>/<str:file_name>',
            SubmissionPrivateMediaView.as_view(), name='serve_private_media'
        ),
    ])),
    path('<int:submission_pk>/', include([
        path('', include('opentech.apply.review.urls', namespace="reviews")),
        path('revisions/', include(revision_urls, namespace="revisions")),
    ])),
    path('', include('opentech.apply.determinations.urls', namespace="determinations")),
    path('<slug:status>/', SubmissionsByStatus.as_view(), name='status'),
], 'submissions')

rounds_urls = ([
    path('', RoundListView.as_view(), name="list"),
    path('<int:pk>/', SubmissionsByRound.as_view(), name="detail"),
], 'rounds')


urlpatterns = [
    path('submissions/', include(submission_urls)),
    path('rounds/', include(rounds_urls)),
    path('projects/', include(projects_urls)),
]
