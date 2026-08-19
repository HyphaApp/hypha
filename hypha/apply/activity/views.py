import json

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView
from django_ratelimit.decorators import ratelimit
from rolepermissions.checkers import has_object_permission

from hypha.apply.activity.forms import CommentForm
from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.funds.models.submissions import ApplicationSubmission
from hypha.apply.funds.permissions import user_can_view_post_comment_form
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


# Models a "mini" comment may be attached to via `related`, mapped to the
# attribute holding the id of the project they belong to (`None` when the object
# *is* the project). Keyed by ContentType `(app_label, model)`.
RELATED_MODEL_PROJECT_ATTRS = {
    ("application_projects", "project"): None,
    ("application_projects", "invoice"): "project_id",
    ("application_projects", "projectsow"): "project_id",
    ("application_projects", "projectformpointer"): "project_id",
    ("project_reports", "report"): "project_id",
}


def _clean_id(value) -> int | None:
    """Coerce a content type/object id from request params, `None` if unusable"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _get_comment_source(params) -> ApplicationSubmission:
    """Resolve the submission a mini comment form is bound to.

    Comments always hang off the submission - every caller of
    `generate_post_comment_url` passes one - so anything else is rejected rather
    than resolved as an arbitrary content type.
    """
    content_type_id = _clean_id(params.get("source_content_type"))
    object_id = _clean_id(params.get("source_object_id"))

    if content_type_id is None or object_id is None:
        raise Http404

    if content_type_id != ContentType.objects.get_for_model(ApplicationSubmission).pk:
        raise Http404

    return get_object_or_404(ApplicationSubmission, pk=object_id)


def _get_comment_project(submission: ApplicationSubmission):
    """The project a submission's comment sidebar hangs off, if there is one.

    Used to keep the comment's related object within the submission's own
    project.
    """
    return submission.projects.first()


def _user_can_comment(user, submission: ApplicationSubmission) -> bool:
    """Whether `user` may use the mini comment form on `submission`

    The same gate `comments_view` applies to the full comment form.
    """
    return user_can_view_post_comment_form(
        user=user, submission=submission
    ) and has_object_permission("view_comments", user, submission)


def _get_comment_related(params, project):
    """Resolve the (optional) object a mini comment is being attached to.

    Restricted to the objects that render a comment sidebar, and to objects
    belonging to the comment's own project.
    """
    raw_content_type = params.get("related_content_type") or ""
    raw_object_id = params.get("related_object_id") or ""

    if not raw_content_type and not raw_object_id:
        return None

    content_type_id = _clean_id(raw_content_type)
    object_id = _clean_id(raw_object_id)
    if content_type_id is None or object_id is None or project is None:
        raise Http404

    content_type = ContentType.objects.filter(pk=content_type_id).first()
    if content_type is None:
        raise Http404

    project_attr_key = (content_type.app_label, content_type.model)
    if project_attr_key not in RELATED_MODEL_PROJECT_ATTRS:
        raise Http404

    related = get_object_or_404(content_type.model_class(), pk=object_id)

    project_attr = RELATED_MODEL_PROJECT_ATTRS[project_attr_key]
    related_project_id = (
        related.pk if project_attr is None else getattr(related, project_attr)
    )
    if related_project_id != project.pk:
        raise Http404

    return related


@login_required
@require_http_methods(["POST", "GET"])
@ratelimit(key="user", rate=settings.DEFAULT_RATE_LIMIT, method="POST")
def post_comment(request: HttpRequest):
    """Render & handle the "mini" comment form shown in object detail sidebars."""
    params = request.POST if request.method == "POST" else request.GET

    source = _get_comment_source(params)
    project = _get_comment_project(source)
    if not _user_can_comment(request.user, source):
        raise PermissionDenied

    related = _get_comment_related(params, project)

    if request.method == "GET":
        form = CommentForm(user=request.user, mini=True)
        form.fields["source_content_type"].initial = ContentType.objects.get_for_model(
            source
        ).pk
        form.fields["source_object_id"].initial = source.pk
        if related is not None:
            form.fields[
                "related_content_type"
            ].initial = ContentType.objects.get_for_model(related).pk
            form.fields["related_object_id"].initial = related.pk
        return render(request, "activity/partials/comment_form.html", {"form": form})

    form = CommentForm(user=request.user, data=request.POST, mini=True)
    form.instance.user = request.user
    form.instance.source = source
    form.instance.type = COMMENT
    form.instance.timestamp = timezone.now()

    if not form.is_valid():
        return render(request, "activity/partials/comment_form.html", {"form": form})

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
