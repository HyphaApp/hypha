from django import template

register = template.Library()


@register.filter
def should_display_primary_actions_block(user, submission):
    review_primary_action_displayed = submission.can_review(user) and (
        submission.in_internal_review_phase or submission.in_external_review_phase
    )
    view_determination_action_displayed = submission.is_finished

    if review_primary_action_displayed or view_determination_action_displayed:
        return True
    else:
        return False


@register.simple_tag
def show_progress_button(user, submission):
    return bool(list(submission.get_actions_for_user(user)))
