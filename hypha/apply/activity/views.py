from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView
from django_ratelimit.decorators import ratelimit

from hypha.apply.funds.models.submissions import ApplicationSubmission
from hypha.apply.users.decorators import staff_required
from hypha.apply.utils.storage import PrivateMediaView
from hypha.apply.utils.views import DelegatedViewMixin

from .filters import NotificationFilter
from .forms import CommentForm
from .messaging import MESSAGES, messenger
from .models import COMMENT, Activity, ActivityAttachment
from .services import get_related_comments_for_user


class ActivityContextMixin:
    """Mixin to add related 'comments' of the current view's 'self.object'"""

    def get_context_data(self, **kwargs):
        extra = {
            # Do not prefetch on the related_object__author as the models
            # are not homogeneous and this will fail
            "comments": get_related_comments_for_user(self.object, self.request.user)
        }
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
            A dict of kwargs to be passed to [`CommentForm`][hypha.apply.activity.forms.CommentForm]. The submission instance is removed from this return, while a boolean of `has_partners` is added based off the submission.
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
        # List only last 30 days' activities
        queryset = Activity.objects.filter(current=True).latest()
        self.filterset = self.filterset_class(self.request.GET, queryset=queryset)
        return self.filterset.qs.distinct().order_by("-timestamp")

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(NotificationsView, self).get_context_data()
        context["filter"] = self.filterset
        return context
