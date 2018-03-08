from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, View


@method_decorator(login_required, name='dispatch')
class ViewDispatcher(View):
    admin_view = None
    applicant_view = None

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_apply_staff:
            view = self.admin_view
        else:
            view = self.applicant_view

        return view.as_view()(request, *args, **kwargs)


class DelegateableView(DetailView):
    """A view which passes its context to child form views to allow them to post to the same URL """
    def get_context_data(self, **kwargs):
        forms = dict(form_view.contribute_form(self.object, self.request.user) for form_view in self.form_views.values())
        return super().get_context_data(
            **forms,
            **kwargs,
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        kwargs['submission'] = self.object

        # Information to pretend we originate from this view
        kwargs['template_names'] = self.get_template_names()
        kwargs['context'] = self.get_context_data()

        form_submitted = request.POST['form-submitted'].lower()
        view = self.form_views[form_submitted].as_view()

        return view(request, *args, **kwargs)


class DelegatedViewMixin(View):
    """For use on create views accepting forms from another view"""
    def get_template_names(self):
        return self.kwargs['template_names']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        # Use the previous context but override the validated form
        form = kwargs.pop('form')
        kwargs.update(self.kwargs['context'])
        kwargs.update(**{self.context_name: form})
        return super().get_context_data(**kwargs)

    @classmethod
    def contribute_form(cls, submission, user):
        return cls.context_name, cls.form_class(instance=submission, user=user)
