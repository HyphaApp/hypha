from django.utils.translation import gettext_lazy as _
from modelcluster.models import ClusterableModel
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.fields import StreamField

from hypha.core.wagtail.admin import register_public_site_setting


class LinkBlock(blocks.StructBlock):
    page = blocks.PageChooserBlock()
    title = blocks.CharBlock(
        help_text=_("Leave blank to use the page's own title"), required=False
    )

    class Meta:
        template = ("navigation/blocks/menu_item.html",)


@register_public_site_setting(icon="", classnames="icon icon-list-ul")
class NavigationSettings(BaseSiteSetting, ClusterableModel):
    primary_navigation = StreamField(
        [
            ("link", LinkBlock()),
        ],
        blank=True,
        help_text=_("Main site navigation"),
        use_json_field=True,
    )

    panels = [
        FieldPanel("primary_navigation"),
    ]
