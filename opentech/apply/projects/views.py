from django.views.generic import DetailView

from opentech.apply.utils.views import ViewDispatcher

from .models import Project


class AdminProjectDetailView(DetailView):
    model = Project
    template_name_suffix = '_admin_detail'


class ApplicantProjectDetailView(DetailView):
    model = Project


class ProjectDetailView(ViewDispatcher):
    admin_view = AdminProjectDetailView
    applicant_view = ApplicantProjectDetailView
