from django.contrib.auth.decorators import login_required
from django.forms.models import ModelForm
from django.http import HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views import defaults
from django.views.generic import View
from django.views.generic.base import ContextMixin
from django.views.generic.detail import SingleObjectTemplateResponseMixin
from django.views.generic.edit import ModelFormMixin, ProcessFormView
from django.shortcuts import redirect


def page_not_found(request, exception=None, template_name='apply/404.html'):
    if not request.user.is_authenticated:
        template_name = '404.html'
    return defaults.page_not_found(request, exception, template_name)


@method_decorator(login_required, name='dispatch')
class ViewDispatcher(View):
    admin_view: View = None
    reviewer_view: View = None
    partner_view: View = None
    community_view: View = None
    applicant_view: View = None

    def admin_check(self, request):
        return request.user.is_apply_staff

    def reviewer_check(self, request):
        return request.user.is_reviewer

    def partner_check(self, request):
        return request.user.is_partner

    def community_check(self, request):
        return request.user.is_community_reviewer

    def dispatch(self, request, *args, **kwargs):
        view = self.applicant_view

        if self.admin_check(request):
            view = self.admin_view
        elif self.reviewer_check(request):
            view = self.reviewer_view
        elif self.partner_check(request):
            view = self.partner_view
        elif self.community_check(request):
            view = self.community_view

        if view:
            return view.as_view()(request, *args, **kwargs)
        return HttpResponseForbidden()


class DelegatableBase(ContextMixin):
    """
    A view which passes its context to child form views to allow them to post to the same URL
    `DelegateableViews` objects should contain form views that inherit from `DelegatedViewMixin`
    and `FormView`
    """
    form_prefix = 'form-submitted-'

    def __init__(self, *args, **kwargs):
        self._form_views = {
            self.form_prefix + form_view.context_name: form_view
            for form_view in self.form_views
        }

    def get_form_kwargs(self):
        return {}

    def get_context_data(self, **kwargs):
        forms = {}
        for form_view in self._form_views.values():
            view = form_view()
            view.setup(self.request, self.args, self.kwargs)
            context_key, form = view.contribute_form(self)
            forms[context_key] = form

        return super().get_context_data(
            form_prefix=self.form_prefix,
            **forms,
            **kwargs,
        )

    def post(self, request, *args, **kwargs):
        # Information to pretend we originate from this view
        kwargs['context'] = self.get_context_data()
        kwargs['template_names'] = self.get_template_names()

        for form_key, form_view in self._form_views.items():
            if form_key in request.POST:
                return form_view.as_view()(request, *args, parent=self, **kwargs)

        # Fall back to get if not form exists as submitted
        return redirect(request.path)


class DelegateableView(DelegatableBase):
    def get_form_kwargs(self):
        return {
            'user': self.request.user,
            'instance': self.object,
        }

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        kwargs['object'] = self.object

        return super().post(request, *args, **kwargs)


class DelegateableListView(DelegatableBase):
    def get_form_kwargs(self):
        return {
            'user': self.request.user,
        }

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        return super().post(request, *args, **kwargs)


class DelegatedViewMixin(View):
    """For use on create views accepting forms from another view"""

    # TODO: REMOVE IN DJANGO 2.2
    def setup(self, request, *args, **kwargs):
        """Initialize attributes shared by all view methods."""
        self.request = request
        self.args = args
        self.kwargs = kwargs

    def get_object(self):
        # Make sure the form instance, bound at the parent class level,  is the same as the
        # value we work with on the class.
        # If we don't have self.object, bind the parent instance to it. This value will then
        # be used by the form. Any further calls to get_object will get a new instance of the object
        if not hasattr(self, 'object'):
            parent_object = self.get_parent_object()
            if isinstance(parent_object, self.model):
                return parent_object

        return super().get_object()

    def get_template_names(self):
        return self.kwargs['template_names']

    def get_form_name(self):
        return self.context_name

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['user'] = self.request.user
        form_kwargs.update(**self.get_parent_kwargs())
        return form_kwargs

    def get_parent_kwargs(self):
        try:
            return self.parent.get_form_kwargs()
        except AttributeError:
            return self.kwargs['parent'].get_form_kwargs()

    def get_parent_object(self):
        return self.get_parent_kwargs()['instance']

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.name = self.get_form_name()
        return form

    def get_context_data(self, **kwargs):
        # Use the previous context but override the validated form
        form = kwargs.pop('form')
        kwargs.update(self.kwargs['context'])
        kwargs.update(**{self.context_name: form})
        return super().get_context_data(**kwargs)

    @classmethod
    def is_model_form(cls):
        return issubclass(cls.form_class, ModelForm)

    def contribute_form(self, parent):
        self.parent = parent

        # We do not want to bind any forms generated this way
        # pretend we are doing a get request to avoid passing data to forms
        old_method = None
        if self.request.method in ('POST', 'PUT'):
            old_method = self.request.method
            self.request.method = 'GET'

        form = self.get_form()

        if old_method:
            self.request.method = old_method
        return self.context_name, form

    def get_success_url(self):
        query = self.request.GET.urlencode()
        if query:
            query = '?' + query
        return self.request.path + query


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
