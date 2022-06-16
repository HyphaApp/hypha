from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView

from hypha.apply.funds.models.submissions import ApplicationSubmission
from hypha.apply.users.decorators import login_required
from hypha.apply.utils.views import DelegatedViewMixin

from .forms import CommentForm
from .messaging import MESSAGES, messenger
from .models import COMMENT, Activity


class ActivityContextMixin:
    def get_context_data(self, **kwargs):
        related_query = self.model.activities.rel.related_query_name
        query = {related_query: self.object}
        extra = {
            # Do not prefetch on the related_object__author as the models
            # are not homogeneous and this will fail
            'actions': Activity.actions.filter(**query).select_related(
                'user',
            ).prefetch_related(
                'related_object',
            ).visible_to(self.request.user),
            'comments': Activity.comments.filter(**query).select_related(
                'user',
            ).prefetch_related(
                'related_object',
            ).visible_to(self.request.user),
        }
        return super().get_context_data(**extra, **kwargs)


class CommentFormView(DelegatedViewMixin, CreateView):
    form_class = CommentForm
    context_name = 'comment_form'

    def form_valid(self, form):
        source = self.kwargs['object']
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
        return self.object.source.get_absolute_url() + '#communications'

    def get_form_kwargs(self):
        # We dont want to pass the submission as the instance
        kwargs = super().get_form_kwargs()
        kwargs.pop('instance')
        return kwargs


@method_decorator(login_required, name='dispatch')
class NotificationsView(ListView):
    model = Activity
    template_name = 'activity/notifications.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(NotificationsView, self).get_context_data()
        user = self.request.user
        if user.is_applicant or user.is_partner:
            context['comments'] = Activity.comments.filter(source__user=user).order_by('-timestamp')
            context['actions'] = Activity.actions.filter(source__user=user).order_by('-timestamp')
        elif user.is_reviewer:
            reviewer_submissions = ApplicationSubmission.objects.filter(reviewers=user).values_list("id", flat=True)
            context['comments'] = Activity.comments.filter(source_object_id__in=reviewer_submissions).order_by('-timestamp')
            context['actions'] = Activity.actions.filter(source_object_id__in=reviewer_submissions).order_by('-timestamp')
        elif user.is_apply_staff or user.is_apply_staff_admin:
            context['comments'] = Activity.comments.all().order_by('-timestamp')
            context['actions'] = Activity.actions.all().order_by('-timestamp')
        else:
            context['comments'] = Activity.comments.filter(user=user).order_by('-timestamp')
            context['actions'] = Activity.actions.filter(user=user).order_by('-timestamp')
        # context['filter'] = NotificationFilter(self.request.GET, queryset=self.get_queryset())
        return context
