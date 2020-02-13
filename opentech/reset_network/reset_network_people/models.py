from django.db import models
from wagtail.admin.edit_handlers import MultiFieldPanel, FieldPanel, StreamFieldPanel
from wagtail.core import blocks
from wagtail.core.fields import StreamField
from wagtail.core.models import Page
from wagtail.snippets.blocks import SnippetChooserBlock
from opentech.reset_network.reset_network_person.models import ResetNetworkPerson


class ResetNetworkPeoplePage(Page):
    class Meta:
        verbose_name = "Reset Network People Page"

    parent_page_types = ['reset_network_home.ResetNetworkHomePage']
    subpage_types = []

    content_heading = models.CharField(verbose_name='Heading', max_length=255, blank=False)
    content_text = models.TextField(verbose_name='Text', blank=True)

    section_1 = StreamField(
        [
            ('sub_heading', blocks.CharBlock(icon='tag')),
            ('persons', blocks.ListBlock(
                blocks.StructBlock([
                    ('person', SnippetChooserBlock(ResetNetworkPerson)),
                ], icon='user'), icon='group'
            )),
        ],
        verbose_name='Content - Section 1 (People)',
        blank=True
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('content_heading'),
            FieldPanel('content_text'),
        ], heading='Content'),
        StreamFieldPanel('section_1'),
    ]
