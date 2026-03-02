from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.views import FilterView

from hypha.apply.users.decorators import staff_required

from ..tables import SubmissionFilterAndSearch

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
        search_term = self.request.GET.get("query")

        if self.object_list.exists():
            submission_count = self.object_list.count()
            submission_values = self.object_list.value()
            count_values = submission_values.get("value__count")
            if total := submission_values.get("value__sum"):
                total_value = total
            else:
                total_value = 0
            if average := submission_values.get("value__avg"):
                average_value = round(average)
            else:
                average_value = 0
        else:
            count_values = 0
            total_value = 0
            average_value = 0
            submission_count = 0

        return super().get_context_data(
            search_term=search_term,
            filter_action=self.filter_action,
            count_values=count_values,
            total_value=total_value,
            average_value=average_value,
            submission_count=submission_count,
            **kwargs,
        )
