import django_tables2 as tables
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django_tables2.views import SingleTableMixin

from hypha.apply.users.decorators import staff_required

from ..models import (
    AssignedReviewers,
    ReviewerRole,
)
from ..tables import StaffAssignmentsTable
from ..workflow import active_statuses

User = get_user_model()


class RoleColumn(tables.Column):
    def render(self, value, record):
        return AssignedReviewers.objects.filter(
            reviewer=record,
            role=self.verbose_name,
            submission__status__in=active_statuses,
        ).count()


@method_decorator(staff_required, name="dispatch")
class StaffAssignments(SingleTableMixin, ListView):
    model = User
    table_class = StaffAssignmentsTable
    table_pagination = False
    template_name = "funds/staff_assignments.html"

    def get_queryset(self):
        # Only list staff.
        return self.model.objects.staff()

    def get_table_data(self):
        table_data = super().get_table_data()
        reviewer_roles = ReviewerRole.objects.all().order_by("order")
        for data in table_data:
            for i, _role in enumerate(reviewer_roles):
                # Only setting column name with dummy value 0.
                # Actual value will be set in RoleColumn render method.
                setattr(data, f"role{i}", 0)
        return table_data

    def get_table_kwargs(self):
        reviewer_roles = ReviewerRole.objects.all().order_by("order")
        extra_columns = []
        for i, role in enumerate(reviewer_roles):
            extra_columns.append((f"role{i}", RoleColumn(verbose_name=role)))
        return {
            "extra_columns": extra_columns,
        }
