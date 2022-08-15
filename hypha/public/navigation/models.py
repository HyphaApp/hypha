from django.utils.translation import gettext_lazy as _
from modelcluster.models import ClusterableModel
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.fields import StreamField


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
        FieldPanel('primary_navigation'),
    ]
