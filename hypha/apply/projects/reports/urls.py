from django.urls import include, path

from .views import (
    ReportDeleteView,
    ReportDetailView,
    ReportEditDueDateView,
    ReportingView,
    ReportListView,
    ReportPrivateMedia,
    ReportSkipView,
    ReportUpdateView,
)

app_name = "reports"

urlpatterns = [
    path("", ReportListView.as_view(), name="submitted"),
    path("all/", ReportingView.as_view(), name="all"),
    path(
        "<int:pk>/",
        include(
            [
                path("", ReportDetailView.as_view(), name="detail"),
                path("skip/", ReportSkipView.as_view(), name="skip"),
                path("edit/", ReportUpdateView.as_view(), name="edit"),
                path(
                    "edit-due-date/",
                    ReportEditDueDateView.as_view(),
                    name="edit_due_date",
                ),
                path(
                    "delete/",
                    ReportDeleteView.as_view(),
                    name="delete",
                ),
                path(
                    "documents/<int:file_pk>/",
                    ReportPrivateMedia.as_view(),
                    name="document",
                ),
            ]
        ),
    ),
]
