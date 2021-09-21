from django.urls import path
from rest_framework_nested import routers

from hypha.apply.api.v1.determination.views import SubmissionDeterminationViewSet
from hypha.apply.api.v1.reminder.views import SubmissionReminderViewSet
from hypha.apply.api.v1.review.views import SubmissionReviewViewSet
from hypha.apply.api.v1.screening.views import (
    ScreeningStatusViewSet,
    SubmissionScreeningStatusViewSet,
)
from hypha.apply.api.v1.projects.views import (
    DeliverableViewSet
)

from .views import (
    CommentViewSet,
    CurrentUser,
    MetaTermsViewSet,
    RoundViewSet,
    SubmissionActionViewSet,
    SubmissionCommentViewSet,
    SubmissionFilters,
    SubmissionViewSet,
)

app_name = 'v1'


router = routers.SimpleRouter()
router.register(r'submissions', SubmissionViewSet, basename='submissions')
router.register(r'comments', CommentViewSet, basename='comments')
router.register(r'rounds', RoundViewSet, basename='rounds')
router.register(r'screening_statuses', ScreeningStatusViewSet, basename='screenings')
router.register(r'meta_terms', MetaTermsViewSet, basename='meta-terms')

submission_router = routers.NestedSimpleRouter(router, r'submissions', lookup='submission')
submission_router.register(r'actions', SubmissionActionViewSet, basename='submission-actions')
submission_router.register(r'comments', SubmissionCommentViewSet, basename='submission-comments')
submission_router.register(r'reviews', SubmissionReviewViewSet, basename='reviews')
submission_router.register(r'determinations', SubmissionDeterminationViewSet, basename='determinations')
submission_router.register(r'screening_statuses', SubmissionScreeningStatusViewSet, basename='submission-screening_statuses')
submission_router.register(r'reminders', SubmissionReminderViewSet, basename='submission-reminder')

invoice_router = routers.NestedSimpleRouter(router, r'invoices', lookup='invoice')
invoice_router.register(r'deliverables', DeliverableViewSet, basename='invoice-deliverables')

urlpatterns = [
    path('user/', CurrentUser.as_view(), name='user'),
    path('submissions_filter/', SubmissionFilters.as_view(), name='submissions-filter')
]

urlpatterns = router.urls + submission_router.urls + invoice_router.urls + urlpatterns
