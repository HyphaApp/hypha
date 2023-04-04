from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from hypha.apply.activity.services import (
    get_related_actions_for_user,
)
from hypha.apply.funds.permissions import has_permission

from .models import ApplicationSubmission


@login_required
@require_GET
def partial_submission_activities(request, pk):
    submission = get_object_or_404(ApplicationSubmission, pk=pk)
    has_permission(
        'submission_view', request.user, object=submission, raise_exception=True
    )
    ctx = {'actions': get_related_actions_for_user(submission, request.user)}
    return render(request, 'activity/include/action_list.html', ctx)
