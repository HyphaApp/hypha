from modelcluster.models import ClusterableModel
from wagtail.admin.edit_handlers import StreamFieldPanel
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.core import blocks
from wagtail.core.fields import StreamField


class ResetNetworkMenusItem(blocks.StructBlock):
    class Meta:
        label = 'Menu item'
        icon = 'doc-empty'

    page = blocks.PageChooserBlock()
    title = blocks.CharBlock(help_text="Leave blank to use the page's own title", required=False)


@register_setting(icon='list-ul')
class ResetNetworkMenusMain(BaseSetting, ClusterableModel):
    class Meta:
        verbose_name = 'Reset Network Main Menu'

    items = StreamField(
        [
            ('item', ResetNetworkMenusItem())
        ],
        verbose_name='Main menu',
        blank=True
    )

    panels = [
        StreamFieldPanel('items'),
    ]


@register_setting(icon='list-ul')
class ResetNetworkMenusFooter(BaseSetting, ClusterableModel):
    class Meta:
        verbose_name = 'Reset Network Footer Menu'

    items = StreamField(
        [
            ('item', ResetNetworkMenusItem())
        ],
        verbose_name='Footer menu',
        blank=True
    )

    panels = [
        StreamFieldPanel('items'),
    ]
