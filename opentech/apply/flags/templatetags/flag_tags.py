from django import template

register = template.Library()


@register.filter
def flagged_by(submission, user):
    return submission.flagged_by(user)


@register.filter
def flagged_staff(submission):
    return submission.flagged_staff
