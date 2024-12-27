from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django_filters.views import FilterView
from django_tables2.paginators import LazyPaginator
from django_tables2.views import SingleTableMixin

from hypha.apply.review.models import Review
from hypha.apply.users.decorators import (
    staff_required,
)

from ..tables import (
    ReviewerLeaderboardDetailTable,
    ReviewerLeaderboardFilter,
    ReviewerLeaderboardTable,
)

User = get_user_model()


@method_decorator(staff_required, name="dispatch")
class ReviewerLeaderboard(SingleTableMixin, FilterView):
    filterset_class = ReviewerLeaderboardFilter
    filter_action = ""
    table_class = ReviewerLeaderboardTable
    table_pagination = False
    template_name = "funds/reviewer_leaderboard.html"

    def get_context_data(self, **kwargs):
        search_term = self.request.GET.get("query")

        return super().get_context_data(
            search_term=search_term,
            filter_action=self.filter_action,
            **kwargs,
        )

    def get_queryset(self):
        # Only list reviewers.
        return self.filterset_class._meta.model.objects.reviewers()

    def get_table_data(self):
        ninety_days_ago = timezone.now() - timedelta(days=90)
        this_year = timezone.now().year
        last_year = timezone.now().year - 1
        return (
            super()
            .get_table_data()
            .annotate(
                total=Count("assignedreviewers__review"),
                ninety_days=Count(
                    "assignedreviewers__review",
                    filter=Q(
                        assignedreviewers__review__created_at__date__gte=ninety_days_ago
                    ),
                ),
                this_year=Count(
                    "assignedreviewers__review",
                    filter=Q(assignedreviewers__review__created_at__year=this_year),
                ),
                last_year=Count(
                    "assignedreviewers__review",
                    filter=Q(assignedreviewers__review__created_at__year=last_year),
                ),
            )
        )


@method_decorator(staff_required, name="dispatch")
class ReviewerLeaderboardDetail(SingleTableMixin, ListView):
    model = Review
    table_class = ReviewerLeaderboardDetailTable
    paginator_class = LazyPaginator
    table_pagination = {"per_page": 25}
    template_name = "funds/reviewer_leaderboard_detail.html"

    def get_context_data(self, **kwargs):
        obj = User.objects.get(pk=self.kwargs.get("pk"))
        return super().get_context_data(object=obj, **kwargs)

    def get_table_data(self):
        return (
            super()
            .get_table_data()
            .filter(author__reviewer_id=self.kwargs.get("pk"))
            .select_related("submission")
        )
