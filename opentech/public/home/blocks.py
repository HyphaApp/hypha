from wagtail.wagtailcore import blocks

from wagtail.wagtailimages.blocks import ImageChooserBlock


class OurWorkBlock(blocks.StructBlock):
    icon = ImageChooserBlock()
    description = blocks.TextBlock(help_text='The first word will be bold')

    class Meta:
        template = 'home/blocks/our_work.html'
