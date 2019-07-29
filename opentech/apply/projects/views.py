from django.utils.decorators import method_decorator
from django.views.generic import DetailView

from opentech.apply.users.decorators import staff_required

from .models import Project


@method_decorator(staff_required, name='dispatch')
class ProjectDetailView(DetailView):
    model = Project
