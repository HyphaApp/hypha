import json

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView
from rolepermissions.checkers import has_object_permission

from hypha.apply.activity.forms import CommentForm
from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.funds.models.submissions import ApplicationSubmission
from hypha.apply.users.decorators import is_apply_staff, staff_required
from hypha.apply.utils.storage import PrivateMediaView

from . import services
from .filters import NotificationFilter
from .models import COMMENT, Activity, ActivityAttachment


@login_required
@require_http_methods(["GET"])
def partial_comments(request, pk: int):
    """
    Render a partial view of comments for a given submission primary key.

    This view handles comments for both submission and (if existing) pulls related project activities.
    It checks the user's permissions and fetches the related comments for the user.
    The comments are paginated and rendered in the 'activity_list' template.

    Args:
        request (HttpRequest): The HTTP request object.
        content_type (str): The type of content ('submission' or 'project').
        pk (int): The primary key of the content object.

    Returns:
        HttpResponse: The rendered 'activity_list' template with the context data.
    """
    submission = get_object_or_404(ApplicationSubmission, pk=pk)
    if not has_object_permission("view_comments", request.user, submission):
        raise PermissionDenied

    editable = not submission.is_archive

    qs = services.get_related_activities_for_user(submission, request.user)
    page = Paginator(qs, per_page=10, orphans=5).page(request.GET.get("page", 1))  # type: ignore[var-annotated]

    ctx = {
        "page": page,
        "activities": page.object_list,
        "editable": editable,
    }
    return render(request, "activity/include/activity_list.html", ctx)


@login_required
def edit_comment(request, pk):
    """Edit a comment."""
    activity = get_object_or_404(Activity, id=pk)

    if activity.type != COMMENT or activity.user != request.user:
        raise PermissionDenied(_("You can only edit your own comments"))

    if activity.deleted:
        raise PermissionDenied(_("You can not edit a deleted comment"))

    if request.GET.get("action") == "cancel":
        return render(
            request,
            "activity/partial_comment_message.html",
            {"activity": activity},
        )

    if request.method == "POST":
        activity = services.edit_comment(activity, request.POST.get("message"))

        return render(
            request,
            "activity/partial_comment_message.html",
            {"activity": activity, "success": True},
        )

    return render(request, "activity/ui/edit_comment_form.html", {"activity": activity})


@login_required
@user_passes_test(is_apply_staff)
def delete_comment(request, pk):
    """Soft delete a comment."""
    activity = get_object_or_404(Activity, id=pk)

    if activity.type != COMMENT or activity.user != request.user:
        raise PermissionDenied(_("You can only delete your own comments"))

    if activity.deleted:
        raise PermissionDenied(_("You can not delete a deleted comment"))

    if request.method == "DELETE":
        activity = services.delete_comment(activity)

        return render(
            request,
            "activity/ui/activity-comment-item.html",
            {"activity": activity, "success": True},
        )

    return render(
        request,
        "activity/ui/activity-comment-item.html",
        {"activity": activity},
    )


def get_object_for_content_type(content_type_id, object_id):
    """Resolve a content type id & object id pair into a model instance.

    Both ids come straight from user input, so anything that doesn't resolve to
    an existing object - missing, non-numeric or dangling ids, or a stale
    ContentType row whose model no longer exists - returns None rather than
    raising.

    Args:
        content_type_id: the pk of the ContentType of the object
        object_id: the pk of the object itself

    Returns:
        The model instance, or None if it could not be resolved
    """
    try:
        content_type = ContentType.objects.get_for_id(int(content_type_id))
    except (TypeError, ValueError, ContentType.DoesNotExist):
        return None

    model_class = content_type.model_class()
    if model_class is None:
        return None

    try:
        return model_class._default_manager.filter(pk=object_id).first()
    except (TypeError, ValueError, ValidationError):
        return None


@login_required
@require_http_methods(["POST", "GET"])
@user_passes_test(is_apply_staff)
def post_comment(request: HttpRequest):
    if request.method == "POST":
        form = CommentForm(user=request.user, data=request.POST or None, mini=True)
        source = get_object_for_content_type(
            request.POST.get("source_content_type"),
            request.POST.get("source_object_id"),
        )
        if source is None:
            raise Http404

        form.instance.user = request.user
        form.instance.source = source
        form.instance.type = COMMENT
        form.instance.timestamp = timezone.now()
        if form.is_valid():
            obj = form.save()
            messenger(
                MESSAGES.COMMENT,
                request=request,
                user=request.user,
                source=source,
                related=obj,
            )
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "commentAdded": obj.pk,
                            "showMessage": mark_safe(_("Comment added!")),
                        }
                    ),
                },
            )
        return render(request, "activity/partials/comment_form.html", {"form": form})
    else:
        form = CommentForm(user=request.user, mini=True)
        params = request.GET.dict()

        # Ensure the provided source content type & object actually exist
        source_content_type = params.get("source_content_type")
        source_object_id = params.get("source_object_id")
        if get_object_for_content_type(source_content_type, source_object_id) is None:
            raise Http404

        form.fields["source_content_type"].initial = source_content_type
        form.fields["source_object_id"].initial = source_object_id

        related_content_type = params.get("related_content_type")
        related_object_id = params.get("related_object_id")
        if (
            get_object_for_content_type(related_content_type, related_object_id)
            is not None
        ):
            form.fields["related_content_type"].initial = related_content_type
            form.fields["related_object_id"].initial = related_object_id

        return render(request, "activity/partials/comment_form.html", {"form": form})


class ActivityContextMixin:
    """Mixin to add related 'comments' of the current view's 'self.object'"""

    def get_context_data(self, **kwargs):
        # Comments for both projects and applications exist under the original application
        if isinstance(self.object, ApplicationSubmission):
            application_obj = self.object
        else:
            application_obj = self.object.submission

        extra = {
            "comments_count": services.get_comment_count(
                application_obj, self.request.user
            )
        }
        return super().get_context_data(**extra, **kwargs)


class AttachmentView(PrivateMediaView):
    model = ActivityAttachment

    def dispatch(self, *args, **kwargs):
        file_pk = kwargs.get("file_pk")
        self.instance = get_object_or_404(ActivityAttachment, uuid=file_pk)
        activity = self.instance.activity
        if activity.visibility not in Activity.visibility_for(self.request.user):
            raise PermissionDenied
        return super().dispatch(*args, **kwargs)

    def get_media(self, *args, **kwargs):
        return self.instance.file


@method_decorator(staff_required, name="dispatch")
class NotificationsView(ListView):
    model = Activity
    template_name = "activity/notifications.html"
    filterset_class = NotificationFilter

    def get_queryset(self):
        queryset = Activity.objects.filter(current=True).latest()

        # filter by one month by default
        date_filter = self.request.GET.get("date", "month")

        self.filterset = self.filterset_class(
            {"date": date_filter}
            if date_filter not in self.request.GET
            else self.request.GET,
            queryset=queryset,
        )
        return self.filterset.qs.distinct().order_by("-timestamp", "source_object_id")

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        context["filter"] = self.filterset
        return context
