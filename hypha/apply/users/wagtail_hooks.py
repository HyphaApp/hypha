from django.conf.urls import url
from django.urls import reverse

from wagtail.core import hooks

from opentech.apply.utils.notifications import slack_notify

from .admin_views import index


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^users/$', index, name='index'),
    ]


@hooks.register('after_create_user')
def notify_after_create_user(request, user):
    slack_notify(
        message=f'{request.user} has crated a new account for {user}.',
        request=request,
        related=user,
        path=reverse('wagtailusers_users:edit', args=(user.id,))
    )


@hooks.register('after_edit_user')
def notify_after_edit_user(request, user):
    roles = list(user.groups.values_list('name', flat=True))
    if user.is_superuser:
        roles.append('Administrator')
    if roles:
        roles = ', '.join(roles)
        slack_notify(
            message=f'{request.user} has edited the account for {user} that now have these roles: {roles}.',
            request=request,
            related=user,
            path=reverse('wagtailusers_users:edit', args=(user.id,))
        )
