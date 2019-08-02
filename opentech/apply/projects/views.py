from copy import copy

from django.utils.decorators import method_decorator
from django.views.generic import DetailView, UpdateView

from opentech.apply.activity.messaging import MESSAGES, messenger
from opentech.apply.utils.views import DelegateableView, DelegatedViewMixin
from opentech.apply.users.decorators import staff_required
from opentech.apply.utils.views import ViewDispatcher

from .forms import UpdateProjectLeadForm
from .models import Project


@method_decorator(staff_required, name='dispatch')
class UpdateLeadView(DelegatedViewMixin, UpdateView):
    model = Project
    form_class = UpdateProjectLeadForm
    context_name = 'lead_form'

    def form_valid(self, form):
        # Fetch the old lead from the database
        old = copy(self.get_object())

        response = super().form_valid(form)

        messenger(
            MESSAGES.UPDATE_PROJECT_LEAD,
            request=self.request,
            user=self.request.user,
            submission=form.instance.submission,
            related=old.lead,
            project=form.instance,
        )

        return response


class AdminProjectDetailView(DelegateableView, DetailView):
    form_views = [UpdateLeadView]
    model = Project
    template_name_suffix = '_admin_detail'


class ApplicantProjectDetailView(DetailView):
    model = Project


class ProjectDetailView(ViewDispatcher):
    admin_view = AdminProjectDetailView
    applicant_view = ApplicantProjectDetailView
