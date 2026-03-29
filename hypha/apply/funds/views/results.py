from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.views import FilterView

from hypha.apply.funds.models.submissions import ApplicationSubmissionSkeleton
from hypha.apply.users.decorators import staff_required

from ..tables import SubmissionFilterAndSearch, SubmissionSkeletonFilter

User = get_user_model()


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
        averages_sum = 0
        submission_count = 0

        qs_list = [self.object_list]

        # If a filter comes up that is not applicable to skeleton applications, remove them the results (ie. "lead")
        non_skeleton_fields = set(SubmissionFilterAndSearch.declared_filters) - set(
            SubmissionSkeletonFilter.declared_filters
        )
        if not set(self.request.GET) & set(non_skeleton_fields):
            skeleton_qs = SubmissionSkeletonFilter(
                self.request.GET, queryset=ApplicationSubmissionSkeleton.objects.all()
            ).qs
            qs_list.append(skeleton_qs)

        populated_qs_list = [qs for qs in qs_list if qs.exists()]

        for qs in populated_qs_list:
            submission_count += qs.count()
            submission_values = qs.value()
            count_values += submission_values.get("value__count")
            if total := submission_values.get("value__sum"):
                total_value += total
            if average := submission_values.get("value__avg"):
                averages_sum += round(average)

        if qs_list_len := len(populated_qs_list):
            average_value = averages_sum / qs_list_len
        else:
            average_value = 0

        return super().get_context_data(
            filter_action=self.filter_action,
            count_values=count_values,
            total_value=total_value,
            average_value=average_value,
            submission_count=submission_count,
            **kwargs,
        )
