from django.urls import include, path

from .views import (
    CommentEdit,
    CommentList,
    CommentListCreate,
    RoundLabDetail,
    RoundLabList,
    SubmissionAction,
    SubmissionList,
    SubmissionDetail,
)

app_name = 'v1'

urlpatterns = [
    path('submissions/', include(([
        path('', SubmissionList.as_view(), name='list'),
        path('<int:pk>/', SubmissionDetail.as_view(), name='detail'),
        path('<int:pk>/actions/', SubmissionAction.as_view(), name='actions'),
        path('<int:pk>/comments/', CommentListCreate.as_view(), name='comments'),
    ], 'submissions'))),
    path('rounds/', include(([
        path('', RoundLabList.as_view(), name='list'),
        path('<int:pk>/', RoundLabDetail.as_view(), name='detail'),
    ], 'rounds'))),
    path('comments/', include(([
        path('', CommentList.as_view(), name='list'),
        path('<int:pk>/edit/', CommentEdit.as_view(), name='edit'),
    ], 'comments')))
]
