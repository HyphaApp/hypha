from opentech.apply.activity.messaging import messenger, MESSAGES
from opentech.apply.users.models import User


def can_alter_reviewers(instance, user):
    return instance.stage.has_external_review and user == instance.lead


def set_reviewers_fields(instance, user, fields):
    reviewers = instance.reviewers.all()
    submitted_reviewers = User.objects.filter(id__in=instance.reviews.values('author'))

    staff_field = fields['staff_reviewers']
    staff_field.queryset = staff_field.queryset.exclude(id__in=submitted_reviewers)
    staff_field.initial = reviewers

    if can_alter_reviewers(instance, user):
        review_field = fields['reviewer_reviewers']
        review_field.queryset = review_field.queryset.exclude(id__in=submitted_reviewers)
        review_field.initial = reviewers
    else:
        fields.pop('reviewer_reviewers')

    return submitted_reviewers, fields


def save_reviewers_message(old_reviewers, new_reviewers, request, submission):
    """
    Save activity messages for reviewers updates based on old vs new reviewers.
    TODO: need to batch send slack messages for MESSAGES.REVIEWERS_UPDATED
    """
    added = new_reviewers - old_reviewers
    removed = old_reviewers - new_reviewers

    messenger(
        MESSAGES.REVIEWERS_UPDATED,
        request=request,
        user=request.user,
        submission=submission,
        added=added,
        removed=removed,
    )