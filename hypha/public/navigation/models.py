from django.utils.translation import gettext_lazy as _
from modelcluster.models import ClusterableModel
from wagtail.admin.edit_handlers import StreamFieldPanel
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.core import blocks
from wagtail.core.fields import StreamField


class LinkBlock(blocks.StructBlock):
    page = blocks.PageChooserBlock()
    title = blocks.CharBlock(help_text=_("Leave blank to use the page's own title"), required=False)

    class Meta:
        template = 'navigation/blocks/menu_item.html',


@register_setting(icon='', classnames='icon icon-list-ul')
class NavigationSettings(BaseSetting, ClusterableModel):
    primary_navigation = StreamField(
        [('link', LinkBlock()), ],
        blank=True,
        help_text=_('Main site navigation'),
        use_json_field=True,
    )

    panels = [
        StreamFieldPanel('primary_navigation'),
    ]
