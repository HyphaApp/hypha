from django.conf import settings
from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView
from django_tables2 import RequestConfig

from hypha.apply.funds.models import (
    ApplicationSubmission,
    ReviewerSettings,
    RoundsAndLabs,
)
from hypha.apply.funds.permissions import can_export_submissions
from hypha.apply.funds.tables import (
    ReviewerSubmissionsTable,
    SubmissionsTable,
)
from hypha.apply.projects.filters import ProjectListFilter
from hypha.apply.projects.models import Invoice, Project, ProjectSettings
from hypha.apply.projects.models.payment import DECLINED, PAID
from hypha.apply.projects.tables import (
    InvoiceDashboardTable,
    PAFForReviewDashboardTable,
    ProjectsDashboardTable,
)
from hypha.apply.todo.views import render_task_templates_for_user
from hypha.apply.utils.views import ViewDispatcher

from .services import get_paf_for_review


def get_preview_context(queryset, limit=5):
    count = queryset.count()
    return {
        "objects": queryset[:limit],
        "count": count,
        "display_more": count > limit,
    }


class MySubmissionContextMixin:
    def get_context_data(self, **kwargs):
        submissions = ApplicationSubmission.objects.all().for_table(self.request.user)
        my_submissions = (
            submissions.filter(user=self.request.user)
            .active()
            .current()
            .select_related("draft_revision")
        )
        my_submissions = [submission.from_draft() for submission in my_submissions]

        my_inactive_submissions = (
            submissions.filter(user=self.request.user).inactive().current()
        )
        my_inactive_submissions_table = ReviewerSubmissionsTable(
            my_inactive_submissions, prefix="my-submissions-"
        )

        return super().get_context_data(
            my_submissions=my_submissions,
            my_inactive_submissions=my_inactive_submissions_table,
            **kwargs,
        )


class MyFlaggedMixin:
    def my_flagged(self, submissions):
        return get_preview_context(
            queryset=submissions.flagged_by(self.request.user).order_by("-submit_time")
        )


class PAFReviewMixin:
    paf_reviewer_role = None  # set to a user attribute e.g. "is_apply_staff"

    def paf_for_review(self):
        if not getattr(self.request.user, self.paf_reviewer_role, False):
            return {"count": None, "table": None}
        project_settings = ProjectSettings.for_request(self.request)
        paf_approvals = list(
            get_paf_for_review(
                user=self.request.user,
                is_paf_approval_sequential=project_settings.paf_approval_sequential,
            )
        )
        paf_table = PAFForReviewDashboardTable(
            paf_approvals, prefix="paf-review-", order_by="-date_requested"
        )
        RequestConfig(self.request, paginate=False).configure(paf_table)
        return {
            "count": len(paf_approvals),
            "table": paf_table,
        }


class AdminDashboardView(PAFReviewMixin, MyFlaggedMixin, TemplateView):
    template_name = "dashboard/staff_dashboard.html"
    paf_reviewer_role = "is_apply_staff"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submissions = ApplicationSubmission.objects.all().for_table(self.request.user)

        context.update(
            {
                "awaiting_reviews": self.awaiting_reviews(submissions),
                "can_export": can_export_submissions(self.request.user),
                "my_reviewed": get_preview_context(
                    submissions.reviewed_by(self.request.user).order_by("-submit_time")
                ),
                "rounds": self.rounds(),
                "my_flagged": self.my_flagged(submissions),
                "my_tasks": self.my_tasks(),
            }
        )
        if settings.PROJECTS_ENABLED:
            context["projects"] = self.projects()
            context["active_invoices"] = self.active_invoices()
            context["paf_for_review"] = self.paf_for_review()

        return context

    def my_tasks(self):
        tasks = render_task_templates_for_user(self.request, self.request.user)
        return {
            "count": len(tasks),
            "data": tasks,
        }

    def awaiting_reviews(self, submissions):
        submissions = submissions.in_review_for(self.request.user).order_by(
            "-submit_time"
        )
        count = submissions.count()

        limit = 5
        return {
            "count": count,
            "display_more": count > limit,
            "submissions": submissions[:limit],
        }

    def active_invoices(self):
        invoices = list(
            Invoice.objects.filter(
                project__lead=self.request.user,
            )
            .in_progress()
            .select_related("project")
        )

        return {
            "count": len(invoices),
            "table": InvoiceDashboardTable(invoices),
        }

    def projects(self):
        projects = Project.objects.filter(lead=self.request.user).for_table()

        filterset = ProjectListFilter(
            data=self.request.GET or None, request=self.request, queryset=projects
        )

        limit = 10
        projects_count = projects.count()

        return {
            "count": projects_count,
            "filterset": filterset,
            "table": ProjectsDashboardTable(data=projects[:limit], prefix="project-"),
            "display_more": projects_count > limit,
            "url": reverse("apply:projects:all"),
        }

    def rounds(self):
        limit = 6
        rounds = (
            RoundsAndLabs.objects.with_progress()
            .active()
            .order_by("-end_date")
            .by_lead(self.request.user)
        )

        return {
            "closed": rounds.closed()[:limit],
            "open": rounds.open()[:limit],
        }


class FinanceDashboardView(PAFReviewMixin, MyFlaggedMixin, TemplateView):
    template_name = "dashboard/finance_dashboard.html"
    paf_reviewer_role = "is_finance"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "active_invoices": self.active_invoices(),
                "invoices_for_approval": self.invoices_for_approval(),
                "invoices_to_convert": self.invoices_to_convert(),
                "paf_for_review": self.paf_for_review(),
                "my_tasks": self.my_tasks(),
            }
        )

        return context

    def my_tasks(self):
        tasks = render_task_templates_for_user(self.request, self.request.user)
        return {
            "count": len(tasks),
            "data": tasks,
        }

    def active_invoices(self):
        invoices = list(Invoice.objects.for_finance_1().select_related("project"))
        return {
            "count": len(invoices),
            "table": InvoiceDashboardTable(invoices),
        }

    def invoices_for_approval(self):
        invoices = list(Invoice.objects.approved_by_staff().select_related("project"))
        return {"count": len(invoices), "table": InvoiceDashboardTable(invoices)}

    def invoices_to_convert(self):
        invoices = list(Invoice.objects.waiting_to_convert().select_related("project"))
        return {
            "count": len(invoices),
            "table": InvoiceDashboardTable(invoices),
        }


class ReviewerDashboardView(MyFlaggedMixin, MySubmissionContextMixin, TemplateView):
    template_name = "dashboard/reviewer_dashboard.html"

    def get(self, request, *args, **kwargs):
        # redirect to submissions list when we use the filter to search for something
        if len(request.GET):
            query_str = "?"
            for key, value in request.GET.items():
                query_str += key + "=" + value + "&"
            return HttpResponseRedirect(
                reverse_lazy("funds:submissions:list") + query_str
            )

        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        """
        If use_settings variable is set for ReviewerSettings use settings
        parameters to filter submissions or return all as it
        was by default.
        """
        reviewer_settings = ReviewerSettings.for_request(self.request)
        if reviewer_settings.use_settings:
            submissions = ApplicationSubmission.objects.for_reviewer_settings(
                self.request.user, reviewer_settings
            ).for_table(self.request.user)
        else:
            submissions = ApplicationSubmission.objects.all().for_table(
                self.request.user
            )

        context.update(
            {
                "awaiting_reviews": self.awaiting_reviews(submissions),
                "my_reviewed": get_preview_context(
                    submissions.reviewed_by(self.request.user).order_by("-submit_time")
                ),
                "my_flagged": self.my_flagged(submissions),
            }
        )

        return context

    def awaiting_reviews(self, submissions):
        submissions = submissions.in_review_for(self.request.user).order_by(
            "-submit_time"
        )
        count = submissions.count()

        limit = 5
        return {
            "count": count,
            "display_more": count > limit,
            "submissions": submissions[:limit],
        }


class ContractingDashboardView(PAFReviewMixin, MyFlaggedMixin, TemplateView):
    template_name = "dashboard/contracting_dashboard.html"
    paf_reviewer_role = "is_contracting"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "projects_in_contracting": self.projects_in_contracting(),
                "paf_for_review": self.paf_for_review(),
                "my_tasks": self.my_tasks(),
            }
        )

        return context

    def my_tasks(self):
        tasks = render_task_templates_for_user(self.request, self.request.user)
        return {
            "count": len(tasks),
            "data": tasks,
        }

    def projects_in_contracting(self):
        if not self.request.user.is_contracting:
            return {
                "count": None,
                "waiting_for_contract": {
                    "count": None,
                    "table": None,
                },
                "waiting_for_contract_approval": {
                    "count": None,
                    "table": None,
                },
            }
        projects_in_contracting = Project.objects.in_contracting()
        waiting_for_contract = list(
            projects_in_contracting.filter(contracts__isnull=True).for_table()
        )
        waiting_for_contract_approval = list(
            projects_in_contracting.filter(contracts__isnull=False).for_table()
        )
        return {
            "count": len(waiting_for_contract) + len(waiting_for_contract_approval),
            "waiting_for_contract": {
                "count": len(waiting_for_contract),
                "table": ProjectsDashboardTable(
                    data=waiting_for_contract, prefix="project-waiting-contract-"
                ),
            },
            "waiting_for_contract_approval": {
                "count": len(waiting_for_contract_approval),
                "table": ProjectsDashboardTable(
                    data=waiting_for_contract_approval,
                    prefix="project-waiting-approval-",
                ),
            },
        }


class CommunityDashboardView(MySubmissionContextMixin, TemplateView):
    template_name = "dashboard/community_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submissions = ApplicationSubmission.objects.all().for_table(self.request.user)

        # Submissions in community review phase
        my_community_review, my_community_review = self.my_community_review(
            self.request.user, submissions
        )
        context.update(
            {
                "my_community_review": my_community_review,
                "my_community_review_count": my_community_review.count(),
                "my_reviewed": get_preview_context(
                    submissions.reviewed_by(self.request.user).order_by("-submit_time")
                ),
            }
        )

        return context

    def my_community_review(self, user, submissions):
        my_community_review = submissions.in_community_review(user).order_by(
            "-submit_time"
        )
        my_community_review_table = ReviewerSubmissionsTable(
            my_community_review, prefix="my-community-review-"
        )

        return my_community_review, my_community_review_table


class ApplicantDashboardView(TemplateView):
    template_name = "dashboard/applicant_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["my_submissions_exists"] = ApplicationSubmission.objects.filter(
            Q(user=self.request.user) | Q(co_applicants__user=self.request.user)
        ).exists()

        # Number of items to show in skeleton in each section of lazy loading
        context["per_section_items"] = range(3)

        context["my_projects_exists"] = Project.objects.filter(
            user=self.request.user
        ).exists()
        context["active_invoices"] = self.active_invoices()
        context["historical_projects"] = self.historical_project_data()
        context["historical_submissions"] = self.historical_submission_data()
        context["my_tasks"] = self.my_tasks()
        return context

    def my_tasks(self):
        tasks = render_task_templates_for_user(self.request, self.request.user)
        return {
            "count": len(tasks),
            "data": tasks,
        }

    def active_invoices(self):
        active_invoices = list(
            Invoice.objects.filter(project__user=self.request.user)
            .exclude(status__in=[PAID, DECLINED])
            .order_by("-requested_at")
        )
        return {"count": len(active_invoices), "data": active_invoices}

    def historical_project_data(self):
        historical_projects = list(
            Project.objects.filter(user=self.request.user).complete().for_table()
        )
        return {
            "count": len(historical_projects),
            "table": ProjectsDashboardTable(
                data=historical_projects, prefix="past-project-"
            ),
        }

    def historical_submission_data(self):
        historical_submissions = list(
            ApplicationSubmission.objects.filter(
                user=self.request.user,
            )
            .inactive()
            .current()
            .for_table(self.request.user)
        )
        return {
            "count": len(historical_submissions),
            "table": SubmissionsTable(data=historical_submissions),
        }


class DashboardView(ViewDispatcher):
    admin_view = AdminDashboardView
    reviewer_view = ReviewerDashboardView
    community_view = CommunityDashboardView
    applicant_view = ApplicantDashboardView
    finance_view = FinanceDashboardView
    contracting_view = ContractingDashboardView

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        # Handle the case when there is no dashboard for the user
        # and redirect them to the home page of apply site.
        # Suggestion: create a dedicated dashboard for user without any role.
        if isinstance(response, HttpResponseForbidden):
            return HttpResponseRedirect("/")

        return response
