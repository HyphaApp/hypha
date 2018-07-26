from django.views.generic import CreateView

from opentech.apply.utils.views import DelegatedViewMixin

from .forms import CommentForm
from .messaging import messenger, MESSAGES
from .models import Activity, COMMENT


ACTIVITY_LIMIT = 50


class AllActivityContextMixin:
    def get_context_data(self, **kwargs):
        extra = {
            'actions': Activity.actions.filter(submission__in=self.object_list)[:ACTIVITY_LIMIT],
            'comments': Activity.comments.filter(submission__in=self.object_list[:ACTIVITY_LIMIT]),
            'all_activity': Activity.objects.filter(submission__in=self.object_list)[:ACTIVITY_LIMIT],
        }
        return super().get_context_data(**extra, **kwargs)


class ActivityContextMixin:
    def get_context_data(self, **kwargs):
        extra = {
            'actions': Activity.actions.filter(submission=self.object),
            'comments': Activity.comments.filter(submission=self.object).visible_to(self.request.user),
        }

        return super().get_context_data(**extra, **kwargs)


class CommentFormView(DelegatedViewMixin, CreateView):
    form_class = CommentForm
    context_name = 'comment_form'

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.submission = self.kwargs['submission']
        form.instance.type = COMMENT
        response = super().form_valid(form)
        messenger(
            MESSAGES.COMMENT,
            request=self.request,
            user=self.request.user,
            submission=self.object.submission,
            comment=self.object,
        )
        return response

    def get_success_url(self):
        return self.object.submission.get_absolute_url() + '#communications'

    @classmethod
    def contribute_form(cls, submission, user):
        # We dont want to pass the submission as the instance
        return super().contribute_form(None, user=user)
