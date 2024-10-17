from django.urls import include, path

from .views import AttachmentView, NotificationsView, edit_comment, partial_comments

app_name = "activity"


urlpatterns = [
    path("anymail/", include("anymail.urls")),
    path("notifications/", NotificationsView.as_view(), name="notifications"),
    path(
        "comments/<content_type>-<int:pk>/", partial_comments, name="partial-comments"
    ),
    path("<pk>/edit-comment/", edit_comment, name="edit-comment"),
    path(
        "activities/attachment/<uuid:file_pk>/download/",
        AttachmentView.as_view(),
        name="attachment",
    ),
]
