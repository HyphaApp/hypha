from django.views.generic import CreateView
from django.utils import timezone

from opentech.apply.utils.views import DelegatedViewMixin

from .forms import CommentForm
from .messaging import messenger, MESSAGES
from .models import Activity, COMMENT


ACTIVITY_LIMIT = 50


class AllActivityContextMixin:
    def get_context_data(self, **kwargs):
        extra = {
            'actions': Activity.actions.select_related(
                'user',
            ).prefetch_related(
                'source',
            )[:ACTIVITY_LIMIT],
            'comments': Activity.comments.select_related(
                'user',
            ).prefetch_related(
                'source',
            )[:ACTIVITY_LIMIT],
            'all_activity': Activity.objects.select_related(
                'user',
            ).prefetch_related(
                'source',
            )[:ACTIVITY_LIMIT],
        }
        return super().get_context_data(**extra, **kwargs)


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
