from django.apps import AppConfig
from django.conf import settings


class UserNewsletterSignupConfig(AppConfig):
    name = "extensions.ots.user_newsletter_signup"
    label = "extension_user_newsletter_signup"

    def ready(self):
        from extensions.django_hooks.templatehook import hook

        from .template_hooks import hypha_extension_head, wagtail_user_edit

        hook.register("wagtail_user_edit", wagtail_user_edit)
        hook.register("hypha_extension_head", hypha_extension_head)

        from django.forms.fields import BooleanField

        from hypha.apply.users.forms import ProfileForm

        ProfileForm.Meta.fields.append("newsletter_signup")
        field = BooleanField(
            required=False,
            label="Yes, I'd like to receive occasional emails from %s about their mission and programs."
            % settings.ORG_SHORT_NAME,
        )
        field.widget.attrs.update({"class": "profile_newsletter_signup"})
        ProfileForm.base_fields["newsletter_signup"] = field
