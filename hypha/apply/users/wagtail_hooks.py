from django.apps import apps
from django.conf import settings
from wagtail import hooks
from wagtail.models import Site

from hypha.apply.activity.messaging import MESSAGES, messenger

from .utils import send_activation_email, update_is_staff


@hooks.register("after_create_user")
def notify_after_create_user(request, user):
    messenger(
        MESSAGES.STAFF_ACCOUNT_CREATED,
        request=request,
        user=request.user,
        source=user,
    )

    site = Site.find_for_request(request)
    send_activation_email(user, site)


@hooks.register("after_edit_user")
def notify_after_edit_user(request, user):
    roles = list(user.groups.values_list("name", flat=True))
    if user.is_superuser:
        roles.append("Administrator")
    if roles:
        roles = ", ".join(roles)
        messenger(
            MESSAGES.STAFF_ACCOUNT_EDITED,
            request=request,
            user=request.user,
            source=user,
            roles=roles,
        )


@hooks.register("before_delete_user")
def anonymize_delete_user_submissions(request, user):
    if (
        settings.SUBMISSION_SKELETONING_ENABLED
        and request.method == "POST"
        and request.POST.get("handle_subs") == "anon"
    ):
        ApplicationSubmissionSkeleton = apps.get_model(
            "funds", "ApplicationSubmissionSkeleton"
        )

        submissions_to_skeleton = list(
            user.applicationsubmission_set.values(
                "form_data", "page_id", "round_id", "status", "submit_time"
            )
        )

        for submission_dict in submissions_to_skeleton:
            ApplicationSubmissionSkeleton.from_dict(submission_dict)


# Handle setting of `is_staff` after updating a user
hooks.register("after_create_user", update_is_staff)
hooks.register("after_edit_user", update_is_staff)
