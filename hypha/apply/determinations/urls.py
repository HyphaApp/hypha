from django.urls import path

from .views import (
    BatchDeterminationCreateView,
    DeterminationCreateOrUpdateView,
    DeterminationDetailView,
    DeterminationEditView,
)

app_name = "determinations"

urlpatterns = [
    path(
        "<int:submission_pk>/determination/<int:pk>/",
        DeterminationDetailView.as_view(),
        name="detail",
    ),
    path(
        "<int:submission_pk>/determination/<int:pk>/edit/",
        DeterminationEditView.as_view(),
        name="edit",
    ),
    path(
        "<int:submission_pk>/determination/add/",
        DeterminationCreateOrUpdateView.as_view(),
        name="form",
    ),
    path("batch-determine/", BatchDeterminationCreateView.as_view(), name="batch"),
]
