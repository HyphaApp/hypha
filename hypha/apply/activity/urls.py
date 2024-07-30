from django.urls import include, path

from .views import AttachmentView, NotificationsView, get_activity_assgined_user

app_name = "activity"


urlpatterns = [
    path("anymail/", include("anymail.urls")),
    path("notifications/", NotificationsView.as_view(), name="notifications"),
    path(
        "activities/attachment/<uuid:file_pk>/download/",
        AttachmentView.as_view(),
        name="attachment",
    ),
    path("activity/<int:pk>/assigned/", get_activity_assgined_user, name="assigned"),
]
