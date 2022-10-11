from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from hypha.public.utils.blocks import StoryBlock


class AwesomeTableWidgetBlock(blocks.StructBlock):
    table_id = blocks.CharBlock(
        classname="title",
        help_text=_('Please enter only table id from embed code. Table widget code creates automatically.')
    )

    class Meta:
        icon = "table"
        template = "news/blocks/awesome_table_widget_block.html"


class NewsStoryBlock(StoryBlock):
    awesome_table_widget = AwesomeTableWidgetBlock()
