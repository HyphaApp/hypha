import django_filters as filters
from django import forms
from django.contrib.auth import get_user_model

from opentech.apply.funds.tables import (
    Select2ModelMultipleChoiceFilter,
    Select2MultipleChoiceFilter,
    get_used_funds
)

from .models import (
    PROJECT_STATUS_CHOICES,
    REQUEST_STATUS_CHOICES,
    PaymentRequest,
    Project
)

User = get_user_model()


def get_project_leads(request):
    return User.objects.filter(lead_projects__isnull=False).distinct()


class PaymentRequestListFilter(filters.FilterSet):
    fund = Select2ModelMultipleChoiceFilter(label='Funds', queryset=get_used_funds, field_name='project__submission__page')
    status = Select2MultipleChoiceFilter(label='Status', choices=REQUEST_STATUS_CHOICES)
    lead = Select2ModelMultipleChoiceFilter(label='Lead', queryset=get_project_leads, field_name='project__lead')

    class Meta:
        fields = ['lead', 'fund', 'status']
        model = PaymentRequest


class ProjectListFilter(filters.FilterSet):
    fund = Select2ModelMultipleChoiceFilter(label='Funds', queryset=get_used_funds)
    lead = Select2ModelMultipleChoiceFilter(label='Lead', queryset=get_project_leads)
    status = Select2MultipleChoiceFilter(label='Status', choices=PROJECT_STATUS_CHOICES)
    query = filters.CharFilter(field_name='title', lookup_expr="icontains", widget=forms.HiddenInput)

    class Meta:
        fields = ['status', 'lead', 'fund']
        model = Project
