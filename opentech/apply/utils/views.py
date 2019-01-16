from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import defaults
from django.views.generic import DetailView, View
from django.views.generic.detail import SingleObjectTemplateResponseMixin
from django.views.generic.edit import ModelFormMixin, ProcessFormView


def page_not_found(request, exception=None, template_name='apply/404.html'):
    if not request.user.is_authenticated:
        template_name = '404.html'
    return defaults.page_not_found(request, exception, template_name)


@method_decorator(login_required, name='dispatch')
class ViewDispatcher(View):
    admin_view: View = None
    reviewer_view: View = None
    applicant_view: View = None

    def admin_check(self, request):
        return request.user.is_apply_staff

    def reviewer_check(self, request):
        return request.user.is_reviewer

    def dispatch(self, request, *args, **kwargs):
        view = self.applicant_view

        if self.admin_check(request):
            view = self.admin_view
        elif self.reviewer_check(request):
            view = self.reviewer_view

        return view.as_view()(request, *args, **kwargs)


class DelegateableView(DetailView):
    """A view which passes its context to child form views to allow them to post to the same URL """
    form_prefix = 'form-submitted-'

    def get_context_data(self, **kwargs):
        forms = dict(form_view.contribute_form(self.object, self.request.user) for form_view in self.form_views)
        return super().get_context_data(
            form_prefix=self.form_prefix,
            **forms,
            **kwargs,
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        kwargs['submission'] = self.object

        # Information to pretend we originate from this view
        kwargs['template_names'] = self.get_template_names()
        kwargs['context'] = self.get_context_data()

        for form_view in self.form_views:
            if self.form_prefix + form_view.context_name in request.POST:
                return form_view.as_view()(request, *args, **kwargs)

        # Fall back to get if not form exists as submitted
        return self.get(request, *args, **kwargs)


class DelegatedViewMixin(View):
    """For use on create views accepting forms from another view"""
    def get_template_names(self):
        return self.kwargs['template_names']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.name = self.context_name
        return form

    def get_context_data(self, **kwargs):
        # Use the previous context but override the validated form
        form = kwargs.pop('form')
        kwargs.update(self.kwargs['context'])
        kwargs.update(**{self.context_name: form})
        return super().get_context_data(**kwargs)

    @classmethod
    def contribute_form(cls, submission, user):
        form = cls.form_class(instance=submission, user=user)
        form.name = cls.context_name
        return cls.context_name, form


class CreateOrUpdateView(SingleObjectTemplateResponseMixin, ModelFormMixin, ProcessFormView):

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except self.model.DoesNotExist:
            self.object = None

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except self.model.DoesNotExist:
            self.object = None

        return super().post(request, *args, **kwargs)
