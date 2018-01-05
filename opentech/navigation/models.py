from modelcluster.models import ClusterableModel
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.wagtailadmin.edit_handlers import StreamFieldPanel
from wagtail.wagtailcore import blocks
from wagtail.wagtailcore.fields import StreamField

from opentech.esi import purge_esi


class LinkBlock(blocks.StructBlock):
    page = blocks.PageChooserBlock()
    title = blocks.CharBlock(help_text="Leave blank to use the page's own title", required=False)

    class Meta:
        template = 'navigation/blocks/menu_item.html',


class LinkColumnWithHeader(blocks.StructBlock):
    heading = blocks.CharBlock(required=False, help_text="Leave blank if no header required.")
    links = blocks.ListBlock(LinkBlock())

    class Meta:
        template = 'navigation/blocks/footer_column.html',


@register_setting(icon='list-ul')
class NavigationSettings(BaseSetting, ClusterableModel):
    primary_navigation = StreamField(
        [('link', LinkBlock()), ],
        blank=True,
        help_text="Main site navigation"
    )
    secondary_navigation = StreamField(
        [('link', LinkBlock()), ],
        blank=True,
        help_text="Alternative navigation"
    )
    footer_navigation = StreamField(
        [('column', LinkColumnWithHeader()), ],
        blank=True,
        help_text="Multiple columns of footer links with optional header."
    )
    footer_links = StreamField(
        [('link', LinkBlock()), ],
        blank=True,
        help_text="Single list of elements at the base of the page."
    )

    panels = [
        StreamFieldPanel('primary_navigation'),
        StreamFieldPanel('secondary_navigation'),
        StreamFieldPanel('footer_navigation'),
        StreamFieldPanel('footer_links'),
    ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        purge_esi()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        purge_esi()
