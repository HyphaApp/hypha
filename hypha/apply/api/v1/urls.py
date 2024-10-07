from django.urls import path
from rest_framework_nested import routers

from hypha.apply.api.v1.determination.views import SubmissionDeterminationViewSet
from hypha.apply.api.v1.projects.views import InvoiceDeliverableViewSet
from hypha.apply.api.v1.reminder.views import SubmissionReminderViewSet
from hypha.apply.api.v1.review.views import SubmissionReviewViewSet

from .views import (
    CurrentUser,
    RoundViewSet,
    SubmissionActionViewSet,
    SubmissionFilters,
    SubmissionViewSet,
)

app_name = "v1"


router = routers.SimpleRouter()
router.register(r"submissions", SubmissionViewSet, basename="submissions")
router.register(r"rounds", RoundViewSet, basename="rounds")

submission_router = routers.NestedSimpleRouter(
    router, r"submissions", lookup="submission"
)
submission_router.register(
    r"actions", SubmissionActionViewSet, basename="submission-actions"
)
submission_router.register(r"reviews", SubmissionReviewViewSet, basename="reviews")
submission_router.register(
    r"determinations", SubmissionDeterminationViewSet, basename="determinations"
)

submission_router.register(
    r"reminders", SubmissionReminderViewSet, basename="submission-reminder"
)

urlpatterns = [
    path("user/", CurrentUser.as_view(), name="user"),
    path("submissions_filter/", SubmissionFilters.as_view(), name="submissions-filter"),
    path(
        "projects/<int:project_pk>/invoices/<int:invoice_pk>/deliverables/",
        InvoiceDeliverableViewSet.as_view({"post": "create"}),
        name="set-deliverables",
    ),
    path(
        "projects/<int:project_pk>/invoices/<int:invoice_pk>/deliverables/<int:pk>/",
        InvoiceDeliverableViewSet.as_view({"delete": "destroy"}),
        name="remove-deliverables",
    ),
]

urlpatterns = router.urls + submission_router.urls + urlpatterns
