from django.contrib.auth.models import Permission
from wagtail import hooks
from wagtail.admin.admin_url_finder import register_admin_url_finder
from wagtail.contrib.settings.registry import Registry as WagtailSettingsRegistry
from wagtail.contrib.settings.registry import SettingMenuItem, SiteSettingAdminURLFinder
from wagtail.contrib.settings.registry import registry as wagtail_settings_registry
from wagtail.permission_policies import ModelPermissionPolicy


class PublicSiteSettingsRegistry(WagtailSettingsRegistry):
    def register(self, model, **kwargs):
        """
        Register a model as a setting, adding it to the wagtail hypha Settings admin menu
        """

        # Don't bother registering this if it is already registered
        if model in wagtail_settings_registry:
            return model
        wagtail_settings_registry.append(model)

        # Register a new menu item in the "hypha settings" menu
        @hooks.register("register_public_site_setting_menu_item")
        def menu_hook():
            return SettingMenuItem(model, **kwargs)

        @hooks.register("register_permissions")
        def permissions_hook():
            return Permission.objects.filter(
                content_type__app_label=model._meta.app_label,
                codename="change_{}".format(model._meta.model_name),
            )

        # Register an admin URL finder
        permission_policy = ModelPermissionPolicy(model)
        finder_class = type(
            "_SettingsAdminURLFinder",
            (SiteSettingAdminURLFinder,),
            {"model": model, "permission_policy": permission_policy},
        )
        register_admin_url_finder(model, finder_class)

        return model


register_public_site_setting = PublicSiteSettingsRegistry().register_decorator
