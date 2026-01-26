from wagtail.users.apps import WagtailUsersAppConfig


class CustomUsersAppConfig(WagtailUsersAppConfig):
    user_viewset = "hypha.apply.users.admin_views.CustomUserViewSet"
    group_viewset = "hypha.apply.users.admin_views.CustomGroupViewSet"
