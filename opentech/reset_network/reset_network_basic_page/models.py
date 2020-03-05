from opentech.reset_network.reset_network_utils.models import ResetNetworkBasePage
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page


class ResetNetworkBasicPage(ResetNetworkBasePage):
    class Meta:
        verbose_name = "Reset Network Basic Page"

    parent_page_types = ['reset_network_home.ResetNetworkHomePage']
    subpage_types = []

    content_text = RichTextField(verbose_name='Text', blank=False)

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('content_text'),
        ], heading='Content'),
    ]
