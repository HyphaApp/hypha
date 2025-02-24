from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from rolepermissions.checkers import has_object_permission

from hypha.apply.activity.forms import CommentForm
from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.activity.models import COMMENT
from hypha.apply.activity.services import (
    get_comment_count,
    get_related_activities_for_user,
)
from hypha.apply.funds.models.submissions import ApplicationSubmission


@login_required
@ratelimit(key="user", rate=settings.DEFAULT_RATE_LIMIT, method="POST")
def comments_view(request, pk):
    submission = get_object_or_404(ApplicationSubmission, pk=pk)

    if not has_object_permission("view_comments", request.user, submission):
        raise PermissionDenied

    activities = get_related_activities_for_user(submission, request.user)
    comments_count = get_comment_count(submission, request.user)

    form = CommentForm(
        user=request.user,
        submission_partner_list=submission.partners.all(),
        data=request.POST or None,
    )
    if request.method == "POST":
        form.instance.user = request.user
        form.instance.source = submission
        form.instance.type = COMMENT
        form.instance.timestamp = timezone.now()
        if form.is_valid():
            obj = form.save()
            messenger(
                MESSAGES.COMMENT,
                request=request,
                user=request.user,
                source=submission,
                related=obj,
            )
            return redirect("funds:submissions:comments", pk=submission.pk)

    ctx = {
        "object": submission,
        "comments_count": comments_count,
        "activities": activities,
        "form": form,
    }
    return render(
        request,
        "funds/comments.html",
        ctx,
    )
