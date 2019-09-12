from django.contrib.auth import get_user_model
from django_filters import FilterSet

from opentech.apply.funds.tables import (
    Select2ModelMultipleChoiceFilter,
    Select2MultipleChoiceFilter,
    get_used_funds
)

from .models import PROJECT_STATUS_CHOICES, Project


def get_project_leads(request):
    User = get_user_model()
    return User.objects.filter(lead_projects__isnull=False).distinct()


class ProjectListFilter(FilterSet):
    fund = Select2ModelMultipleChoiceFilter(label='Funds', queryset=get_used_funds)
    lead = Select2ModelMultipleChoiceFilter(label='Lead', queryset=get_project_leads)
    status = Select2MultipleChoiceFilter(label='Status', choices=PROJECT_STATUS_CHOICES)

    class Meta:
        fields = ['status', 'lead', 'fund']
        model = Project
