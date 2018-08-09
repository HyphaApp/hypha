from modelcluster.models import ClusterableModel
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.admin.edit_handlers import StreamFieldPanel
from wagtail.core import blocks
from wagtail.core.fields import StreamField

from opentech.public.esi import purge_esi


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

    panels = [
        StreamFieldPanel('primary_navigation'),
    ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        purge_esi()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        purge_esi()
