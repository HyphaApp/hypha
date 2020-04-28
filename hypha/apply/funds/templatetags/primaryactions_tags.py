from django import template

register = template.Library()


@register.filter
def should_display_primary_actions_block(user, submission):
    review_primary_action_displayed = submission.can_review(user) and (submission.in_internal_review_phase or submission.in_external_review_phase)

    if review_primary_action_displayed:
        return True
    else:
        return False
