from django.conf import settings
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView

from hypha.apply.funds.models import (
    ApplicationSubmission,
    ReviewerSettings,
    RoundsAndLabs,
)
from hypha.apply.funds.tables import (
    ReviewerSubmissionsTable,
    SubmissionFilterAndSearch,
    SubmissionReviewerFilterAndSearch,
    SubmissionsTable,
    SummarySubmissionsTable,
    SummarySubmissionsTableWithRole,
    review_filter_for_user,
)
from hypha.apply.projects.filters import ProjectListFilter
from hypha.apply.projects.models import Invoice, PAFApprovals, Project, ProjectSettings
from hypha.apply.projects.models.project import WAITING_FOR_APPROVAL
from hypha.apply.projects.permissions import has_permission
from hypha.apply.projects.tables import (
    InvoiceDashboardTable,
    ProjectsAssigneeDashboardTable,
    ProjectsDashboardTable,
)
from hypha.apply.utils.views import ViewDispatcher


class MySubmissionContextMixin:
    def get_context_data(self, **kwargs):
        submissions = ApplicationSubmission.objects.all().for_table(self.request.user)
        my_submissions = submissions.filter(
            user=self.request.user
        ).active().current().select_related('draft_revision')
        my_submissions = [
            submission.from_draft() for submission in my_submissions
        ]

        my_inactive_submissions = submissions.filter(user=self.request.user).inactive().current()
        my_inactive_submissions_table = ReviewerSubmissionsTable(
            my_inactive_submissions, prefix='my-submissions-'
        )

        return super().get_context_data(
            my_submissions=my_submissions,
            my_inactive_submissions=my_inactive_submissions_table,
            **kwargs,
        )


class MyFlaggedMixin:
    def my_flagged(self, submissions):
        submissions = submissions.flagged_by(self.request.user).order_by('-submit_time')
        row_attrs = dict({'data-flag-type': 'user'}, **SummarySubmissionsTable._meta.row_attrs)

        limit = 5
        return {
            'table': SummarySubmissionsTable(submissions[:limit], prefix='my-flagged-', attrs={'class': 'all-submissions-table flagged-table'}, row_attrs=row_attrs),
            'display_more': submissions.count() > limit,
        }


class AdminDashboardView(MyFlaggedMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submissions = ApplicationSubmission.objects.all().for_table(self.request.user)

        context.update({
            'active_invoices': self.active_invoices(),
            'awaiting_reviews': self.awaiting_reviews(submissions),
            'my_reviewed': self.my_reviewed(submissions),
            'projects': self.projects(),
            'paf_waiting_for_approval': self.paf_waiting_for_approval(),
            'rounds': self.rounds(),
            'my_flagged': self.my_flagged(submissions),
            'paf_waiting_for_assignment': self.paf_waiting_for_approver_assignment(),
        })

        return context

    def awaiting_reviews(self, submissions):
        submissions = submissions.in_review_for(self.request.user).order_by('-submit_time')
        count = submissions.count()

        limit = 5
        return {
            'active_statuses_filter': ''.join(f'&status={status}' for status in review_filter_for_user(self.request.user)),
            'count': count,
            'display_more': count > limit,
            'table': SummarySubmissionsTableWithRole(submissions[:limit], prefix='my-review-'),
        }

    def active_invoices(self):
        invoices = Invoice.objects.filter(
            project__lead=self.request.user,
        ).in_progress()

        return {
            'count': invoices.count(),
            'table': InvoiceDashboardTable(invoices),
        }

    def projects(self):
        projects = Project.objects.filter(lead=self.request.user).for_table()

        filterset = ProjectListFilter(
            data=self.request.GET or None, request=self.request, queryset=projects)

        limit = 10

        return {
            'count': projects.count(),
            'filterset': filterset,
            'table': ProjectsDashboardTable(projects[:limit]),
            'display_more': projects.count() > limit,
            'url': reverse('apply:projects:all'),
        }

    def paf_waiting_for_approver_assignment(self):
        project_settings = ProjectSettings.for_request(self.request)

        paf_approvals = PAFApprovals.objects.annotate(
            roles_count=Count('paf_reviewer_role__user_roles')
        ).filter(roles_count=len(list(self.request.user.groups.all())), approved=False, user__isnull=True)

        for role in self.request.user.groups.all():
            paf_approvals = paf_approvals.filter(paf_reviewer_role__user_roles__id=role.id)

        paf_approvals_ids = paf_approvals.values_list('id', flat=True)
        projects = Project.objects.filter(paf_approvals__id__in=paf_approvals_ids).for_table()

        if project_settings.paf_approval_sequential:
            all_projects = list(projects)
            for project in all_projects:
                matched_paf_approval = paf_approvals.filter(project=project).order_by(
                    'paf_reviewer_role__sort_order').first()
                if project.paf_approvals.filter(
                    paf_reviewer_role__sort_order__lt=matched_paf_approval.paf_reviewer_role.sort_order,
                    approved=False).exists():
                    projects = projects.exclude(id=project.id)

        return {
            'count': projects.count(),
            'table': ProjectsAssigneeDashboardTable(projects),
        }

    def paf_waiting_for_approval(self):
        if not self.request.user.is_apply_staff or not PAFApprovals.objects.filter(
            project__status=WAITING_FOR_APPROVAL,
            user=self.request.user,
        ).exists():
            return {
                'count': None,
                'awaiting_your_approval': {
                    'count': None,
                    'table': None,
                },
                'approved_by_you': {
                    'count': None,
                    'table': None,
                }
            }

        waiting_paf_approval = Project.objects.waiting_for_approval().for_table()
        project_settings = ProjectSettings.for_request(self.request)
        if project_settings.paf_approval_sequential:
            awaiting_user_approval = []
            for waiting_project in waiting_paf_approval.filter(paf_approvals__approved=False):
                permission, _ = has_permission(
                    'paf_status_update',
                    self.request.user,
                    object=waiting_project,
                    raise_exception=False,
                    request=self.request
                )
                if permission:
                    awaiting_user_approval.append(waiting_project)
        else:
            awaiting_user_approval = waiting_paf_approval.filter(
                paf_approvals__user=self.request.user,
                paf_approvals__approved=False,
            )
        approved_by_user = waiting_paf_approval.filter(
            paf_approvals__user=self.request.user,
            paf_approvals__approved=True,
        )

        return {
            'count': waiting_paf_approval.count(),
            'awaiting_your_approval': {
                'count': len(awaiting_user_approval),
                'table': ProjectsDashboardTable(data=awaiting_user_approval),
            },
            'approved_by_you': {
                'count': len(approved_by_user),
                'table': ProjectsDashboardTable(data=approved_by_user),
            }
        }

    def my_reviewed(self, submissions):
        """Staff reviewer's reviewed submissions for 'Previous reviews' block"""
        submissions = submissions.reviewed_by(self.request.user).order_by('-submit_time')

        limit = 5
        return {
            'filterset': SubmissionFilterAndSearch(
                data=self.request.GET or None, request=self.request, queryset=submissions),
            'table': SummarySubmissionsTableWithRole(submissions[:limit], prefix='my-review-'),
            'display_more': submissions.count() > limit,
            'url': reverse('funds:submissions:list'),
        }

    def rounds(self):
        limit = 6
        rounds = RoundsAndLabs.objects.with_progress().active().order_by('-end_date').by_lead(
            self.request.user)
        return {
            'closed': rounds.closed()[:limit],
            'open': rounds.open()[:limit],
        }


class FinanceDashboardView(MyFlaggedMixin, TemplateView):
    template_name = 'dashboard/finance_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'active_invoices': self.active_invoices(),
            'invoices_for_approval': self.invoices_for_approval(),
            'invoices_to_convert': self.invoices_to_convert(),
            'paf_waiting_for_approval': self.paf_waiting_for_approval(),
            'paf_waiting_for_assignment': self.paf_waiting_for_approver_assignment(),
        })

        return context

    def active_invoices(self):
        if self.request.user.is_finance_level_2:
            invoices = Invoice.objects.for_finance_2()
        else:
            invoices = Invoice.objects.for_finance_1()

        return {
            'count': invoices.count(),
            'table': InvoiceDashboardTable(invoices),
        }

    def paf_waiting_for_approver_assignment(self):
        project_settings = ProjectSettings.for_request(self.request)

        paf_approvals = PAFApprovals.objects.annotate(
                roles_count=Count('paf_reviewer_role__user_roles')
            ).filter(roles_count=len(list(self.request.user.groups.all())), approved=False, user__isnull=True)

        for role in self.request.user.groups.all():
            paf_approvals = paf_approvals.filter(paf_reviewer_role__user_roles__id=role.id)

        paf_approvals_ids = paf_approvals.values_list('id', flat=True)
        projects = Project.objects.filter(paf_approvals__id__in=paf_approvals_ids).for_table()

        if project_settings.paf_approval_sequential:
            all_projects = list(projects)
            for project in all_projects:
                matched_paf_approval = paf_approvals.filter(project=project).order_by('paf_reviewer_role__sort_order').first()
                if project.paf_approvals.filter(paf_reviewer_role__sort_order__lt=matched_paf_approval.paf_reviewer_role.sort_order, approved=False).exists():
                    projects = projects.exclude(id=project.id)

        return {
            'count': projects.count(),
            'table': ProjectsAssigneeDashboardTable(projects),
        }

    def invoices_for_approval(self):
        if self.request.user.is_finance_level_2:
            invoices = Invoice.objects.approved_by_finance_1()
        else:
            invoices = Invoice.objects.approved_by_staff()

        return {
            'count': invoices.count(),
            'table': InvoiceDashboardTable(invoices)
        }

    def invoices_to_convert(self):
        if settings.INVOICE_EXTENDED_WORKFLOW and self.request.user.is_finance_level_1:
            return {
                'count': None,
                'table': None,
            }
        invoices = Invoice.objects.waiting_to_convert()
        return {
            'count': invoices.count(),
            'table': InvoiceDashboardTable(invoices),
        }

    def paf_waiting_for_approval(self):
        if not self.request.user.is_finance or not PAFApprovals.objects.filter(
            project__status=WAITING_FOR_APPROVAL,
            user=self.request.user,
        ).exists():
            return {
                'count': None,
                'awaiting_your_approval': {
                    'count': None,
                    'table': None,
                },
                'approved_by_you': {
                    'count': None,
                    'table': None,
                }
            }

        waiting_paf_approval = Project.objects.waiting_for_approval().for_table()
        project_settings = ProjectSettings.for_request(self.request)
        if project_settings.paf_approval_sequential:
            awaiting_user_approval = []
            for waiting_project in waiting_paf_approval.filter(paf_approvals__approved=False):
                permission, _ = has_permission(
                    'paf_status_update',
                    self.request.user,
                    object=waiting_project,
                    raise_exception=False,
                    request=self.request
                )
                if permission:
                    awaiting_user_approval.append(waiting_project)
        else:
            awaiting_user_approval = waiting_paf_approval.filter(
                paf_approvals__user=self.request.user,
                paf_approvals__approved=False,
            )
        approved_by_user = waiting_paf_approval.filter(
            paf_approvals__user=self.request.user,
            paf_approvals__approved=True,
        )

        return {
            'count': waiting_paf_approval.count(),
            'awaiting_your_approval': {
                'count': len(awaiting_user_approval),
                'table': ProjectsDashboardTable(data=awaiting_user_approval),
            },
            'approved_by_you': {
                'count': len(approved_by_user),
                'table': ProjectsDashboardTable(data=approved_by_user),
            }
        }


class ReviewerDashboardView(MyFlaggedMixin, MySubmissionContextMixin, TemplateView):
    template_name = 'dashboard/reviewer_dashboard.html'

    def get(self, request, *args, **kwargs):
        # redirect to submissions list when we use the filter to search for something
        if len(request.GET):
            query_str = '?'
            for key, value in request.GET.items():
                query_str += key + '=' + value + '&'
            return HttpResponseRedirect(reverse_lazy('funds:submissions:list') + query_str)

        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        '''
        If use_settings variable is set for ReviewerSettings use settings
        parameters to filter submissions or return all as it
        was by default.
        '''
        reviewer_settings = ReviewerSettings.for_request(self.request)
        if reviewer_settings.use_settings:
            submissions = ApplicationSubmission.objects.for_reviewer_settings(self.request.user, reviewer_settings).for_table(self.request.user)
        else:
            submissions = ApplicationSubmission.objects.all().for_table(self.request.user)

        context.update({
            'awaiting_reviews': self.awaiting_reviews(submissions),
            'my_reviewed': self.my_reviewed(submissions),
            'my_flagged': self.my_flagged(submissions),
            'paf_waiting_for_assignment': self.paf_waiting_for_approver_assignment(),
        })

        return context

    def awaiting_reviews(self, submissions):
        submissions = submissions.in_review_for(self.request.user).order_by('-submit_time')
        count = submissions.count()

        limit = 5
        return {
            'active_statuses_filter': ''.join(f'&status={status}' for status in review_filter_for_user(self.request.user)),
            'count': count,
            'display_more': count > limit,
            'table': ReviewerSubmissionsTable(submissions[:limit], prefix='my-review-'),
        }

    def paf_waiting_for_approver_assignment(self):
        project_settings = ProjectSettings.for_request(self.request)

        paf_approvals = PAFApprovals.objects.annotate(
                roles_count=Count('paf_reviewer_role__user_roles')
            ).filter(roles_count=len(list(self.request.user.groups.all())), approved=False, user__isnull=True)

        for role in self.request.user.groups.all():
            paf_approvals = paf_approvals.filter(paf_reviewer_role__user_roles__id=role.id)

        paf_approvals_ids = paf_approvals.values_list('id', flat=True)
        projects = Project.objects.filter(paf_approvals__id__in=paf_approvals_ids).for_table()

        if project_settings.paf_approval_sequential:
            all_projects = list(projects)
            for project in all_projects:
                matched_paf_approval = paf_approvals.filter(project=project).order_by('paf_reviewer_role__sort_order').first()
                if project.paf_approvals.filter(paf_reviewer_role__sort_order__lt=matched_paf_approval.paf_reviewer_role.sort_order, approved=False).exists():
                    projects = projects.exclude(id=project.id)

        return {
            'count': projects.count(),
            'table': ProjectsAssigneeDashboardTable(projects),
        }

    def my_reviewed(self, submissions):
        """Staff reviewer's reviewed submissions for 'Previous reviews' block"""
        submissions = submissions.reviewed_by(self.request.user).order_by('-submit_time')

        limit = 5
        return {
            'filterset': SubmissionReviewerFilterAndSearch(
                data=self.request.GET or None, request=self.request, queryset=submissions),
            'table': ReviewerSubmissionsTable(submissions[:limit], prefix='my-review-'),
            'display_more': submissions.count() > limit,
            'url': reverse('funds:submissions:list'),
        }


class PartnerDashboardView(MySubmissionContextMixin, TemplateView):
    template_name = 'dashboard/partner_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submissions = ApplicationSubmission.objects.all().for_table(self.request.user)

        # Submissions in which user added as partner
        partner_submissions, partner_submissions_table = self.partner_submissions(self.request.user, submissions)

        context.update({
            'partner_submissions': partner_submissions_table,
            'partner_submissions_count': partner_submissions.count(),
        })

        return context

    def partner_submissions(self, user, submissions):
        partner_submissions = submissions.partner_for(user).order_by('-submit_time')
        partner_submissions_table = SubmissionsTable(partner_submissions, prefix='my-partnered-')

        return partner_submissions, partner_submissions_table


class ContractingDashboardView(MyFlaggedMixin, TemplateView):
    template_name = 'dashboard/contracting_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'paf_waiting_for_approval': self.paf_waiting_for_approval(),
            'projects_in_contracting': self.projects_in_contracting(),
            'paf_waiting_for_assignment': self.paf_waiting_for_approver_assignment(),
        })

        return context

    def paf_waiting_for_approval(self):
        if not self.request.user.is_contracting or not PAFApprovals.objects.filter(
            project__status=WAITING_FOR_APPROVAL,
            user=self.request.user,
        ).exists():
            return {
                'count': None,
                'awaiting_your_approval': {
                    'count': None,
                    'table': None,
                },
                'approved_by_you': {
                    'count': None,
                    'table': None,
                }
            }

        waiting_paf_approval = Project.objects.waiting_for_approval().for_table()
        project_settings = ProjectSettings.for_request(self.request)
        if project_settings.paf_approval_sequential:
            awaiting_user_approval = []
            for waiting_project in waiting_paf_approval.filter(paf_approvals__approved=False):
                permission, _ = has_permission(
                    'paf_status_update',
                    self.request.user,
                    object=waiting_project,
                    raise_exception=False,
                    request=self.request
                )
                if permission:
                    awaiting_user_approval.append(waiting_project)
        else:
            awaiting_user_approval = waiting_paf_approval.filter(
                paf_approvals__user=self.request.user,
                paf_approvals__approved=False,
            )
        approved_by_user = waiting_paf_approval.filter(
            paf_approvals__user=self.request.user,
            paf_approvals__approved=True,
        )

        return {
            'count': waiting_paf_approval.count(),
            'awaiting_your_approval': {
                'count': len(awaiting_user_approval),
                'table': ProjectsDashboardTable(data=awaiting_user_approval),
            },
            'approved_by_you': {
                'count': len(approved_by_user),
                'table': ProjectsDashboardTable(data=approved_by_user),
            }
        }

    def paf_waiting_for_approver_assignment(self):
        project_settings = ProjectSettings.for_request(self.request)

        paf_approvals = PAFApprovals.objects.annotate(
                roles_count=Count('paf_reviewer_role__user_roles')
            ).filter(roles_count=len(list(self.request.user.groups.all())), approved=False, user__isnull=True)

        for role in self.request.user.groups.all():
            paf_approvals = paf_approvals.filter(paf_reviewer_role__user_roles__id=role.id)

        paf_approvals_ids = paf_approvals.values_list('id', flat=True)
        projects = Project.objects.filter(paf_approvals__id__in=paf_approvals_ids).for_table()

        if project_settings.paf_approval_sequential:
            all_projects = list(projects)
            for project in all_projects:
                matched_paf_approval = paf_approvals.filter(project=project).order_by('paf_reviewer_role__sort_order').first()
                if project.paf_approvals.filter(paf_reviewer_role__sort_order__lt=matched_paf_approval.paf_reviewer_role.sort_order, approved=False).exists():
                    projects = projects.exclude(id=project.id)

        return {
            'count': projects.count(),
            'table': ProjectsAssigneeDashboardTable(projects),
        }

    def projects_in_contracting(self):
        if not self.request.user.is_contracting:
            return {
                'count': None,
                'waiting_for_contract': {
                    'count': None,
                    'table': None,
                },
                'waiting_for_contract_approval': {
                    'count': None,
                    'table': None,
                }
            }
        projects_in_contracting = Project.objects.in_contracting()
        waiting_for_contract = projects_in_contracting.filter(contracts__isnull=True).for_table()
        waiting_for_contract_approval = projects_in_contracting.filter(contracts__isnull=False).for_table()
        return {
            'count': projects_in_contracting.count(),
            'waiting_for_contract': {
                'count': waiting_for_contract.count(),
                'table': ProjectsDashboardTable(data=waiting_for_contract)
            },
            'waiting_for_contract_approval': {
                'count': waiting_for_contract_approval.count(),
                'table': ProjectsDashboardTable(data=waiting_for_contract_approval)
            }
        }


class CommunityDashboardView(MySubmissionContextMixin, TemplateView):
    template_name = 'dashboard/community_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submissions = ApplicationSubmission.objects.all().for_table(self.request.user)

        # Submissions in community review phase
        my_community_review, my_community_review = self.my_community_review(self.request.user, submissions)

        # Partner's reviewed submissions
        my_reviewed = self.my_reviewed(self.request, submissions)

        context.update({
            'my_community_review': my_community_review,
            'my_community_review_count': my_community_review.count(),
            'my_reviewed': my_reviewed
        })

        return context

    def my_community_review(self, user, submissions):
        my_community_review = submissions.in_community_review(user).order_by('-submit_time')
        my_community_review_table = ReviewerSubmissionsTable(my_community_review, prefix='my-community-review-')

        return my_community_review, my_community_review_table

    def my_reviewed(self, request, submissions):
        return ReviewerSubmissionsTable(submissions.reviewed_by(request.user).order_by('-submit_time'), prefix='my-reviewed-')


class ApplicantDashboardView(TemplateView):
    template_name = 'dashboard/applicant_dashboard.html'

    def get_context_data(self, **kwargs):
        my_active_submissions = list(self.my_active_submissions(self.request.user))

        context = super().get_context_data(**kwargs)
        context['my_active_submissions'] = my_active_submissions
        context['active_projects'] = self.active_project_data()
        context['historical_projects'] = self.historical_project_data()
        context['historical_submissions'] = self.historical_submission_data()
        return context

    def active_project_data(self):
        active_projects = Project.objects.filter(user=self.request.user).active().for_table()
        return {
            'count': active_projects.count(),
            'table': ProjectsDashboardTable(data=active_projects),
        }

    def my_active_submissions(self, user):
        active_subs = ApplicationSubmission.objects.filter(
            user=user,
        ) .active().current().select_related('draft_revision')

        for submission in active_subs:
            yield submission.from_draft()

    def historical_project_data(self):
        historical_projects = Project.objects.filter(user=self.request.user).complete().for_table()
        return {
            'count': historical_projects.count(),
            'table': ProjectsDashboardTable(data=historical_projects),
        }

    def historical_submission_data(self):
        historical_submissions = ApplicationSubmission.objects.filter(
            user=self.request.user,
        ).inactive().current().for_table(self.request.user)
        return {
            'count': historical_submissions.count(),
            'table': SubmissionsTable(data=historical_submissions)
        }


class DashboardView(ViewDispatcher):
    admin_view = AdminDashboardView
    reviewer_view = ReviewerDashboardView
    partner_view = PartnerDashboardView
    community_view = CommunityDashboardView
    applicant_view = ApplicantDashboardView
    finance_view = FinanceDashboardView
    contracting_view = ContractingDashboardView
