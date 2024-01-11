from wagtail import blocks
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageChooserBlock


class ImageBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    caption = blocks.CharBlock(required=False)

    class Meta:
        icon = "image"
        template = "blocks/image_block.html"


class DocumentBlock(blocks.StructBlock):
    document = DocumentChooserBlock()
    title = blocks.CharBlock(required=False)

    class Meta:
        icon = "doc-full-inverse"
        template = "blocks/document_block.html"


class QuoteBlock(blocks.StructBlock):
    quote = blocks.CharBlock(classname="title")
    attribution = blocks.CharBlock(required=False)
    job_title = blocks.CharBlock(required=False)

    class Meta:
        icon = "openquote"
        template = "blocks/quote_block.html"


class BoxBlock(blocks.StructBlock):
    box_content = blocks.RichTextBlock()
    box_class = blocks.CharBlock(required=False)

    class Meta:
        icon = "placeholder"
        template = "blocks/box_block.html"


class MoreBlock(blocks.StructBlock):
    more_content = blocks.RichTextBlock()
    more_content_more = blocks.RichTextBlock()
    more_class = blocks.CharBlock(required=False)

    class Meta:
        icon = "doc-full"
        template = "blocks/more_block.html"


class ApplyLinkBlock(blocks.StructBlock):
    application = blocks.PageChooserBlock()

    class Meta:
        icon = "link"
        template = "blocks/apply_link_block.html"


# Main streamfield block to be inherited by Pages
class StoryBlock(blocks.StreamBlock):
    heading = blocks.CharBlock(classname="full title", icon="title")
    paragraph = blocks.RichTextBlock()
    box = BoxBlock()
    more = MoreBlock()
    apply_link = ApplyLinkBlock()
    image = ImageBlock()
    quote = QuoteBlock()
    embed = EmbedBlock()
    document = DocumentBlock()

    class Meta:
        template = "blocks/stream_block.html"
