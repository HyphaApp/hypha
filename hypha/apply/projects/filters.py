import django_filters as filters
from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from hypha.apply.funds.tables import (
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
    get_used_funds,
)

from .models.disbursement import Disbursement
from .models.invoice import INVOICE_STATUS_CHOICES, Invoice
from .models.project import (
    CLOSING,
    INVOICING_AND_REPORTING,
    PROJECT_STATUS_CHOICES,
    Contract,
    Project,
)
from .reports.filters import DateRangeInputWidget

User = get_user_model()

REPORTING_CHOICES = (
    (0, _("Up to date")),
    (1, _("Behind schedule")),
)


def get_project_leads(request):
    return User.objects.filter(lead_projects__isnull=False).distinct()


def get_project_contractors(request):
    return User.objects.filter(owned_projects__isnull=False).distinct()


class InvoiceListFilter(filters.FilterSet):
    fund = ModelMultipleChoiceFilter(
        label=_("Funds"),
        queryset=get_used_funds,
        field_name="project__submission__page",
    )
    status = MultipleChoiceFilter(label=_("Status"), choices=INVOICE_STATUS_CHOICES)
    lead = ModelMultipleChoiceFilter(
        label=_("Lead"), queryset=get_project_leads, field_name="project__lead"
    )

    class Meta:
        fields = ["lead", "fund", "status"]
        model = Invoice


class ProjectListFilter(filters.FilterSet):
    project_fund = ModelMultipleChoiceFilter(
        field_name="submission__page", label=_("Funds"), queryset=get_used_funds
    )
    project_lead = ModelMultipleChoiceFilter(
        field_name="lead", label=_("Lead"), queryset=get_project_leads
    )
    project_contractor = ModelMultipleChoiceFilter(
        field_name="user", label=_("Contractor"), queryset=get_project_contractors
    )
    project_status = MultipleChoiceFilter(
        field_name="status", label=_("Status"), choices=PROJECT_STATUS_CHOICES
    )
    query = filters.CharFilter(
        field_name="title", lookup_expr="icontains", widget=forms.HiddenInput
    )
    reporting = MultipleChoiceFilter(
        choices=REPORTING_CHOICES,
        method="filter_reporting",
        field_name="reporting",
        label=_("Reporting"),
    )

    # Maps the public exclude keys (which match the table column names) to this
    # filterset's field names, so a single key in PROJECTS_TABLE_EXCLUDED_FIELDS
    # hides both the table column and its matching filter. Keys without a filter
    # (e.g. "end_date") simply have no effect here.
    COLUMN_TO_FILTER = {
        "fund": "project_fund",
        "lead": "project_lead",
        "status": "project_status",
        "contractor": "project_contractor",
    }

    class Meta:
        fields = [
            "project_status",
            "project_lead",
            "project_contractor",
            "project_fund",
        ]
        model = Project

    def __init__(self, *args, exclude=None, **kwargs):
        if exclude is None:
            exclude = []

        super().__init__(*args, **kwargs)

        exclude = {self.COLUMN_TO_FILTER.get(field, field) for field in exclude}

        self.filters = {
            field: filter
            for field, filter in self.filters.items()
            if field not in exclude
        }

    def filter_reporting(self, queryset, name, value):
        if value == "1":
            return queryset.filter(outstanding_reports__gt=0)
        return queryset.filter(
            Q(outstanding_reports__lt=1) | Q(outstanding_reports__isnull=True),
            status__in=(INVOICING_AND_REPORTING, CLOSING),
        )


NO_CURRENCY = "none"


def get_currency_choices():
    """Choices for the disbursement currency filter.

    Currency lives on the related Contract, so the choices are the distinct
    codes recorded on contracts, plus an explicit choice for rows whose
    contract carries no code (they must remain filterable on their own so a
    single-currency total stays reachable).

    Called per FilterSet instantiation (DB-backed choices) and bound to the
    filter's form field there, because django-filter's choice rendering does
    not resolve callables.

    """
    codes = (
        Contract.objects.filter(currency__isnull=False)
        .values_list("currency", flat=True)
        .distinct()
        .order_by("currency")
    )
    return [(code, code) for code in codes] + [(NO_CURRENCY, _("No currency"))]


class DisbursementListFilter(filters.FilterSet):
    """Filters for the all-disbursements ledger. Minimal by design: date
    range (the disbursement's own date, not the date it was entered),
    currency and project status; more may be added on customer request.

    """

    date = filters.DateFromToRangeFilter(widget=DateRangeInputWidget)
    currency = MultipleChoiceFilter(
        label=_("Currency"),
        method="filter_currency",
    )
    project_status = MultipleChoiceFilter(
        field_name="contract__project__status",
        label=_("Project status"),
        choices=PROJECT_STATUS_CHOICES,
    )

    class Meta:
        fields = ["date", "currency", "project_status"]
        model = Disbursement

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["currency"].field.choices = get_currency_choices()

    def filter_currency(self, queryset, name, value):
        codes = [code for code in value if code != NO_CURRENCY]
        if NO_CURRENCY in value:
            q = Q(contract__currency__isnull=True)
            if codes:
                q |= Q(contract__currency__in=codes)
            return queryset.filter(q)
        if codes:
            return queryset.filter(contract__currency__in=codes)
        return queryset
