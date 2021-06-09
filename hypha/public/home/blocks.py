from django.utils.translation import gettext as _
from wagtail.core import blocks
from wagtail.images.blocks import ImageChooserBlock


class OurWorkBlock(blocks.StructBlock):
    icon = ImageChooserBlock()
    description = blocks.TextBlock(help_text=_('The first word will be bold'))

    class Meta:
        template = 'home/blocks/our_work.html'
