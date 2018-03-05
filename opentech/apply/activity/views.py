from django.utils.decorators import method_decorator
from django.views.generic import CreateView, View

from opentech.apply.users.decorators import staff_required

from .forms import CommentForm
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
            'comments': Activity.comments.filter(submission=self.object),
        }

        return super().get_context_data(**extra, **kwargs)


@method_decorator(staff_required, name='dispatch')
class DelegatedViewMixin(View):
    """For use on create views accepting forms from another view"""
    def get_template_names(self):
        return self.kwargs['template_names']

    def get_context_data(self, **kwargs):
        # Use the previous context but override the validated form
        form = kwargs.pop('form')
        kwargs.update(self.kwargs['context'])
        kwargs.update(**{self.context_name: form})
        return super().get_context_data(**kwargs)

    @classmethod
    def contribute_form(cls, submission):
        return cls.context_name, cls.form_class(instance=submission)


class CommentFormView(DelegatedViewMixin, CreateView):
    form_class = CommentForm
    context_name = 'comment_form'

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.submission = self.kwargs['submission']
        form.instance.type = COMMENT
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.submission.get_absolute_url() + '#communications'

    @classmethod
    def contribute_form(cls, submission):
        # We dont want to pass the submission as the instance
        return super().contribute_form(None)
