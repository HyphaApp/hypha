from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.views import FilterView

from hypha.apply.funds.models.submissions import AnonymizedSubmission
from hypha.apply.users.decorators import staff_required

from ..tables import AnonymizedSubmissionFilter, SubmissionFilterAndSearch

User = get_user_model()

# Fields present in SubmissionFilterAndSearch but not in AnonymizedSubmissionFilter.
# If any of these appear in the request, anonymized submissions cannot be filtered
# consistently, so they are excluded from the results.
_ANONYMIZE_ONLY_FIELDS = frozenset(
    SubmissionFilterAndSearch.declared_filters
) - frozenset(AnonymizedSubmissionFilter.declared_filters)


@method_decorator(cache_page(60), name="dispatch")
@method_decorator(staff_required, name="dispatch")
class SubmissionResultView(FilterView):
    template_name = "funds/submissions_result.html"
    filterset_class = SubmissionFilterAndSearch
    filter_action = ""

    excluded_fields = settings.SUBMISSIONS_TABLE_EXCLUDED_FIELDS

    @property
    def excluded(self):
        return {"exclude": self.excluded_fields}

    def get_filterset_kwargs(self, filterset_class, **kwargs):
        new_kwargs = super().get_filterset_kwargs(filterset_class)
        new_kwargs.update(self.excluded)
        new_kwargs.update(kwargs)
        return new_kwargs

    def get_queryset(self):
        return self.filterset_class._meta.model.objects.current().exclude_draft()

    def get_context_data(self, **kwargs):
        count_values = 0
        total_value = 0
        submission_count = 0

        qs_list = [self.object_list]

        # If a filter is active that has no equivalent on AnonymizedSubmission (e.g. "lead"),
        # anonymized submissions cannot be filtered consistently so exclude them.
        if not set(self.request.GET) & _ANONYMIZE_ONLY_FIELDS:
            anonymized_qs = AnonymizedSubmissionFilter(
                self.request.GET, queryset=AnonymizedSubmission.objects.all()
            ).qs
            qs_list.append(anonymized_qs)

        for qs in qs_list:
            submission_values = qs.value()
            vc = submission_values.get("value__count") or 0
            count_values += vc
            if total := submission_values.get("value__sum"):
                total_value += total
            submission_count += qs.count()

        average_value = round(total_value / count_values) if count_values else 0

        return super().get_context_data(
            filter_action=self.filter_action,
            count_values=count_values,
            total_value=total_value,
            average_value=average_value,
            submission_count=submission_count,
            **kwargs,
        )
