from django.urls import path

from .views import BookmarkSubmissionCreateView

app_name = "bookmarks"

urlpatterns = [
    path(
        "<int:submission_pk>/<type>/bookmark/",
        BookmarkSubmissionCreateView.as_view(),
        name="create_submission_bookmark",
    ),
]
