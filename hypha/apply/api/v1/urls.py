from rest_framework_nested import routers

from .views import (
    CommentViewSet,
    RoundViewSet,
    SubmissionActionViewSet,
    SubmissionCommentViewSet,
    SubmissionViewSet,
)
from .reviews import SubmissionReviewViewSet, ReviewOpinionViewSet

app_name = 'v1'


router = routers.SimpleRouter()
router.register(r'submissions', SubmissionViewSet, basename='submissions')
router.register(r'comments', CommentViewSet, basename='comments')
router.register(r'rounds', RoundViewSet, basename='rounds')

submission_router = routers.NestedSimpleRouter(router, r'submissions', lookup='submission')
submission_router.register(r'actions', SubmissionActionViewSet, basename='submission-actions')
submission_router.register(r'comments', SubmissionCommentViewSet, basename='submission-comments')
submission_router.register(r'reviews', SubmissionReviewViewSet, basename='reviews')

review_router = routers.NestedSimpleRouter(submission_router, r'reviews', lookup='review')
review_router.register(r'opinions', ReviewOpinionViewSet, basename='opinions')

urlpatterns = router.urls + submission_router.urls + review_router.urls
