from modelcluster.models import ClusterableModel
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.admin.edit_handlers import StreamFieldPanel
from wagtail.core import blocks
from wagtail.core.fields import StreamField


class LinkBlock(blocks.StructBlock):
    page = blocks.PageChooserBlock()
    title = blocks.CharBlock(help_text="Leave blank to use the page's own title", required=False)

    class Meta:
        template = 'navigation/blocks/menu_item.html',


@register_setting(icon='list-ul')
class NavigationSettings(BaseSetting, ClusterableModel):
    primary_navigation = StreamField(
        [('link', LinkBlock()), ],
        blank=True,
        help_text="Main site navigation"
    )

    panels = [
        StreamFieldPanel('primary_navigation'),
    ]
