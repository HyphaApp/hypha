from rest_framework_nested import routers

from hypha.apply.api.v1.review.views import SubmissionReviewViewSet

from .views import (
    CommentViewSet,
    RoundViewSet,
    SubmissionActionViewSet,
    SubmissionCommentViewSet,
    SubmissionViewSet,
)

app_name = 'v1'


router = routers.SimpleRouter()
router.register(r'submissions', SubmissionViewSet, basename='submissions')
router.register(r'comments', CommentViewSet, basename='comments')
router.register(r'rounds', RoundViewSet, basename='rounds')

submission_router = routers.NestedSimpleRouter(router, r'submissions', lookup='submission')
submission_router.register(r'actions', SubmissionActionViewSet, basename='submission-actions')
submission_router.register(r'comments', SubmissionCommentViewSet, basename='submission-comments')
submission_router.register(r'reviews', SubmissionReviewViewSet, basename='reviews')

urlpatterns = router.urls + submission_router.urls
