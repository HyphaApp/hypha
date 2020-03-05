from opentech.public.utils.models import SocialFields
from wagtail.core.models import Page


class ResetNetworkBasePage(SocialFields, Page):

    class Meta:
        abstract = True

    promote_panels = (
        Page.promote_panels +
        SocialFields.promote_panels
    )
