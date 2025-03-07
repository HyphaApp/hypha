from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, ListView
from django_ratelimit.decorators import ratelimit

from hypha.apply.funds.models.submissions import ApplicationSubmission
from hypha.apply.funds.permissions import has_permission as has_funds_permission
from hypha.apply.users.decorators import staff_required
from hypha.apply.utils.storage import PrivateMediaView
from hypha.apply.utils.views import DelegatedViewMixin

from . import services
from .filters import NotificationFilter
from .forms import CommentForm
from .messaging import MESSAGES, messenger
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
    obj = get_object_or_404(ApplicationSubmission, pk=pk)
    has_funds_permission(
        "submission_view", request.user, object=obj, raise_exception=True
    )
    editable = not obj.is_archive

    qs = services.get_related_activities_for_user(obj, request.user)
    page = Paginator(qs, per_page=10, orphans=5).page(request.GET.get("page", 1))

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
        raise PermissionError("You can only edit your own comments")

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


class ActivityContextMixin:
    """Mixin to add related 'comments' of the current view's 'self.object'"""

    def get_context_data(self, **kwargs):
        # Do not prefetch on the related_object__author as the models
        # are not homogeneous and this will fail
        activities = services.get_related_activities_for_user(
            self.object, self.request.user
        )

        # Comments for both projects and applications exist under the original application
        if isinstance(self.object, ApplicationSubmission):
            application_obj = self.object
        else:
            application_obj = self.object.submission

        comments_count = services.get_comment_count(application_obj, self.request.user)

        extra = {"activities": activities, "comments_count": comments_count}
        return super().get_context_data(**extra, **kwargs)


@method_decorator(
    ratelimit(key="user", rate=settings.DEFAULT_RATE_LIMIT, method="POST"),
    name="dispatch",
)
class CommentFormView(DelegatedViewMixin, CreateView):
    form_class = CommentForm
    context_name = "comment_form"

    def form_valid(self, form):
        source = self.kwargs["object"]
        form.instance.user = self.request.user
        form.instance.source = source
        form.instance.type = COMMENT
        form.instance.timestamp = timezone.now()
        response = super().form_valid(form)
        messenger(
            MESSAGES.COMMENT,
            request=self.request,
            user=self.request.user,
            source=source,
            related=self.object,
        )
        return response

    def get_success_url(self):
        return self.object.source.get_absolute_url() + "#communications"

    def get_form_kwargs(self) -> dict:
        """Get the kwargs for the [`CommentForm`][hypha.apply.activity.forms.CommentForm].

        Returns:
            A dict of kwargs to be passed to [`CommentForm`][hypha.apply.activity.forms.CommentForm].
            The submission instance is removed from this return, while a boolean of `has_partners` is
            added based off the submission.
        """
        kwargs = super().get_form_kwargs()
        instance = kwargs.pop("instance")
        if isinstance(instance, ApplicationSubmission):
            kwargs["submission_partner_list"] = instance.partners.all()
        return kwargs


class AttachmentView(PrivateMediaView):
    model = ActivityAttachment

    def dispatch(self, *args, **kwargs):
        file_pk = kwargs.get("file_pk")
        self.instance = get_object_or_404(ActivityAttachment, uuid=file_pk)

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
