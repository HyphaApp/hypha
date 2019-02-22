from opentech.apply.utils.image import generate_image_tag

from .models import AssignedReviewers


def save_reviewers_with_roles(submission, role_fields, cleaned_data, alter_external_reviewers=False, submitted_reviewers=None):
    """
    1. Update role reviewers
    2. Update non-role reviewers
        2a. Remove those not on form
        2b. Add in any new non-role reviewers selected
    3. Add in anyone who has already reviewed but who is not selected as a reviewer on the form
    """
    # 1. Update role reviewers
    assigned_roles = {
        role: cleaned_data[field]
        for field, role in role_fields.items()
    }
    for role, reviewer in assigned_roles.items():
        if reviewer:
            AssignedReviewers.objects.update_or_create(
                submission=submission,
                role=role,
                defaults={'reviewer': reviewer},
            )

    # 2. Update non-role reviewers
    # 2a. Remove those not on form
    if alter_external_reviewers:
        reviewers = cleaned_data['reviewer_reviewers']
        assigned_reviewers = submission.assigned.without_roles()
        assigned_reviewers.exclude(
            reviewer__in=reviewers | submitted_reviewers
        ).delete()

        remaining_reviewers = assigned_reviewers.values_list('reviewer_id', flat=True)

        # 2b. Add in any new non-role reviewers selected
        AssignedReviewers.objects.bulk_create(
            AssignedReviewers(
                submission=submission,
                role=None,
                reviewer=reviewer
            ) for reviewer in reviewers
            if reviewer.id not in remaining_reviewers
        )

    # 3. Add in anyone who has already reviewed but who is not selected as a reviewer on the form
    orphaned_reviews = submission.reviews.exclude(
        author__in=submission.assigned.values('reviewer')
    ).select_related('author')

    AssignedReviewers.objects.bulk_create(
        AssignedReviewers(
            submission=submission,
            role=None,
            reviewer=review.author
        ) for review in orphaned_reviews
    )

    return submission


def render_icon(image):
    if not image:
        return ''
    filter_spec = 'fill-20x20'
    return generate_image_tag(image, filter_spec)
