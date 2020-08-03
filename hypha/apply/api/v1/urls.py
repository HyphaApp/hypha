from rest_framework_nested import routers

from .views import (
    CommentViewSet,
    RoundViewSet,
    SubmissionActionViewSet,
    SubmissionCommentViewSet,
    SubmissionViewSet,
)

app_name = 'v1'


router = routers.SimpleRouter()
router.register(r'submissions', SubmissionViewSet, base_name='submissions')
router.register(r'comments', CommentViewSet, base_name='comments')
router.register(r'rounds', RoundViewSet, base_name='rounds')

submission_router = routers.NestedSimpleRouter(router, r'submissions', lookup='submission')
submission_router.register(r'actions', SubmissionActionViewSet, base_name='submission-actions')
submission_router.register(r'comments', SubmissionCommentViewSet, base_name='submission-comments')

urlpatterns = router.urls + submission_router.urls
