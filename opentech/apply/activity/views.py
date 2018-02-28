from django.views.generic import CreateView

from .forms import CommentForm
from .models import Activity


class CommentContextMixin:
    # Adds the comment form to the context
    def get_context_data(self, **kwargs):
        extra = {
            'comments': Activity.objects.filter(application=self.object),
            CommentFormView.context_name: CommentFormView.form_class(),
        }

        return super().get_context_data(**extra, **kwargs)


class DelegatedCreateView(CreateView):
    """For use on create views accepting forms from another view"""
    def get_template_names(self):
        return self.kwargs['template_names']

    def get_context_data(self, **kwargs):
        # Use the previous context but override the validated form
        form = kwargs.pop('form')
        kwargs.update(self.kwargs['context'])
        kwargs.update(**{self.context_name: form})
        return super().get_context_data(**kwargs)


class CommentFormView(DelegatedCreateView):
    form_class = CommentForm
    context_name = 'comment_form'

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.application = self.kwargs['application']
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.application.get_absolute_url()
