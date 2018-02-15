import django_filters as filters
import django_tables2 as tables

from opentech.apply.funds.models import ApplicationSubmission, Round


class DashboardTable(tables.Table):
    submit_time = tables.DateColumn(verbose_name="Submitted")
    status_name = tables.Column(verbose_name="Status")
    stage = tables.Column(verbose_name="Type")
    page = tables.Column(verbose_name="Fund")

    class Meta:
        model = ApplicationSubmission
        fields = ('title', 'status_name', 'stage', 'page', 'round', 'submit_time', 'user')
        template = "dashboard/tables/table.html"

    def render_user(self, value):
        return value.get_full_name()


def get_used_rounds(request):
    return Round.objects.filter(submissions__isnull=False).distinct()


class SubmissionFilter(filters.FilterSet):
    round = filters.ModelMultipleChoiceFilter(queryset=get_used_rounds)

    class Meta:
        model = ApplicationSubmission
        fields = ('round',)
