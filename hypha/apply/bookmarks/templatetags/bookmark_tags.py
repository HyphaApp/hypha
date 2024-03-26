from django import template

register = template.Library()


@register.filter
def bookmarked_by(submission, user):
    return submission.bookmarked_by(user)


@register.filter
def bookmarked_staff(submission):
    return submission.bookmarked_staff
