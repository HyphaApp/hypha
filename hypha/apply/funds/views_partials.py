from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import models
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET
from wagtail.models import Page

from hypha.apply.activity.services import (
    get_related_actions_for_user,
)
from hypha.apply.funds.permissions import has_permission
from hypha.apply.users.groups import REVIEWER_GROUP_NAME, STAFF_GROUP_NAME

from .models import ApplicationSubmission, Round

User = get_user_model()



def sub_menu_funds(request):
    selected_funds = request.GET.getlist("fund")

    # Funds Filter Options
    funds = [{
        'id': f.id,
        'selected': str(f.id) in selected_funds,
        'title': f.title
    } for f in Page.objects.filter(
        applicationsubmission__isnull=False
    ).order_by("title").distinct()]

    ctx = {
        'funds': funds,
        'selected_funds': selected_funds,
    }

    return render(request, "submissions/submenu/funds.html", ctx)


def sub_menu_leads(request):
    selected_leads = request.GET.getlist("lead")

    leads = [{
        'id': item.id,
        'selected': str(item.id) in selected_leads,
        'title': str(item),
        'slack': item.slack,
    } for item in User.objects.filter(
        submission_lead__isnull=False
    ).order_by().distinct()]

    ctx = {
        'leads': leads,
        'selected_leads': selected_leads,
    }

    return render(request, "submissions/submenu/leads.html", ctx)


def sub_menu_rounds(request):
    selected_rounds = request.GET.getlist("round")
    selected_fund = request.GET.get("fund")
    qs = Round.objects.all()

    if selected_fund:
        fund = Page.objects.get(id=selected_fund)
        qs = Round.objects.child_of(fund)

    open_rounds = [{
        'id': item.id,
        'selected': str(item.id) in selected_rounds,
        'title': str(item)
    } for item in qs.open().order_by('-end_date').distinct()]

    closed_rounds = [{
        'id': item.id,
        'selected': str(item.id) in selected_rounds,
        'title': str(item)
    } for item in qs.closed().filter(
        submissions__isnull=False
    ).order_by('-end_date').distinct()]

    ctx = {
        'open_rounds': open_rounds,
        'closed_rounds': closed_rounds,
        'selected_rounds': selected_rounds,
    }

    return render(request, "submissions/submenu/rounds.html", ctx)


def sub_menu_reviewers(request):
    selected_reviewers = request.GET.getlist("reviewers")

    reviewers = [{
        'id': item.id,
        'selected': str(item.id) in selected_reviewers,
        'title': str(item),
        'slack': item.slack,
    } for item in User.objects.filter(
        models.Q(submissions_reviewer__isnull=False) | models.Q(groups__name=STAFF_GROUP_NAME) | models.Q(is_superuser=True)
    ).order_by().distinct()]


    reviewers = sorted(reviewers, key=lambda t: t['selected'], reverse=True)

    ctx = {
        'reviewers': reviewers,
        'selected_reviewers': selected_reviewers,
    }

    return render(request, "submissions/submenu/reviewers.html", ctx)


@login_required
@require_GET
def partial_submission_activities(request, pk):
    submission = get_object_or_404(ApplicationSubmission, pk=pk)
    has_permission(
        'submission_view', request.user, object=submission, raise_exception=True
    )
    ctx = {'actions': get_related_actions_for_user(submission, request.user)}
    return render(request, 'activity/include/action_list.html', ctx)


def partial_reviews(request, pk):
    submission = get_object_or_404(ApplicationSubmission, pk=pk)

    assigned_reviewers = submission.assigned.review_order()

    if not submission.stage.has_external_review:
        assigned_reviewers = assigned_reviewers.staff()

    # Calculate the recommendation based on role and staff reviews
    recommendation = submission.reviews.by_staff().recommendation()

    ctx = {
        'hidden_types': [REVIEWER_GROUP_NAME],
        'staff_reviewers_exist': assigned_reviewers.staff().exists(),
        'assigned_reviewers': assigned_reviewers,
        'recommendation': recommendation,
    }

    return render(request, "funds/includes/review_sidebar.html", ctx)
