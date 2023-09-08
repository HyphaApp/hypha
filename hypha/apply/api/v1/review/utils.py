from django.core.exceptions import PermissionDenied

from hypha.apply.funds.workflow import INITIAL_STATE


def review_workflow_actions(request, submission):
    submission_stepped_phases = submission.workflow.stepped_phases
    action = None
    if submission.status == INITIAL_STATE:
        # Automatically transition the application to "Internal review".
        action = submission_stepped_phases[2][0].name
    elif submission.status == "proposal_discussion":
        # Automatically transition the proposal to "Internal review".
        action = "proposal_internal_review"
    elif (
        submission.status == submission_stepped_phases[2][0].name
        and submission.reviews.count() > 1
    ):
        # Automatically transition the application to "Ready for discussion".
        action = submission_stepped_phases[3][0].name
    elif (
        submission.status == "ext_external_review"
        and submission.reviews.by_reviewers().count() > 1
    ):
        # Automatically transition the application to "Ready for discussion".
        action = "ext_post_external_review_discussion"
    elif (
        submission.status == "com_external_review"
        and submission.reviews.by_reviewers().count() > 1
    ):
        # Automatically transition the application to "Ready for discussion".
        action = "com_post_external_review_discussion"
    elif (
        submission.status == "external_review"
        and submission.reviews.by_reviewers().count() > 1
    ):
        # Automatically transition the proposal to "Ready for discussion".
        action = "post_external_review_discussion"

    # If action is set run perform_transition().
    if action:
        try:
            submission.perform_transition(
                action,
                request.user,
                request=request,
                notify=False,
            )
        except (PermissionDenied, KeyError):
            pass


def get_review_form_fields_for_stage(submission):
    forms = submission.get_from_parent("review_forms").all()
    index = submission.workflow.stages.index(submission.stage)
    try:
        return forms[index].form.form_fields
    except IndexError:
        return forms[0].form.form_fields
