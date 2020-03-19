from wagtail.core.models import Page

from hypha.public.utils.models import SocialFields


class ResetNetworkBasePage(SocialFields, Page):

    class Meta:
        abstract = True

    promote_panels = (
        Page.promote_panels +
        SocialFields.promote_panels
    )
