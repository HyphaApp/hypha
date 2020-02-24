from django.contrib.auth.models import Permission

from wagtail.core import hooks


@hooks.register('register_permissions')
def register_permissions():
    return Permission.objects.filter(
        content_type__app_label='review',
        codename__in=['add_review', 'change_review', 'delete_review']
    )
