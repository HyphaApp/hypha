from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.views import FilterView

from hypha.apply.review.models import Review
from hypha.apply.users.decorators import (
    staff_required,
)

from ..models import (
    ApplicationSubmission,
)
from ..tables import (
    SubmissionFilterAndSearch,
)
from ..utils import (
    format_submission_sum_value,
    is_filter_empty,
)

User = get_user_model()


class SubmissionStatsMixin:
    def get_context_data(self, **kwargs):
        submissions = ApplicationSubmission.objects.exclude_draft()
        filter = kwargs.get("filter")
        user = self.request.user

        # Getting values is an expensive operation. If there's no valid filters
        # then `count_values` & `total_value` will be encapsulating all submissions
        # and should be used rather than recaluclating these values.
        if not filter or not is_filter_empty(filter):
            submission_sum = kwargs.get("total_value")
        else:
            submission_value = submissions.current().value()
            submission_sum = format_submission_sum_value(submission_value)

        submission_undetermined_count = submissions.undetermined().count()
        review_my_count = submissions.reviewed_by(user).count()

        submission_accepted = submissions.current_accepted()
        submission_accepted_value = submission_accepted.value()
        submission_accepted_sum = format_submission_sum_value(submission_accepted_value)
        submission_accepted_count = submission_accepted.count()

        reviews = Review.objects.submitted()
        review_count = reviews.count()
        review_my_score = reviews.by_user(user).score()

        return super().get_context_data(
            submission_undetermined_count=submission_undetermined_count,
            review_my_count=review_my_count,
            submission_sum=submission_sum,
            submission_accepted_count=submission_accepted_count,
            submission_accepted_sum=submission_accepted_sum,
            review_count=review_count,
            review_my_score=review_my_score,
            **kwargs,
        )


@method_decorator(cache_page(60), name="dispatch")
@method_decorator(staff_required, name="dispatch")
class SubmissionResultView(SubmissionStatsMixin, FilterView):
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
            total_value = format_submission_sum_value(submission_values)
            if value := submission_values.get("value__avg"):
                average_value = round(value)
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
