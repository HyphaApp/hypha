from django.core.exceptions import ValidationError
from django.db import models

from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel,
    FieldRowPanel,
    MultiFieldPanel,
    PageChooserPanel,
    StreamFieldPanel,
)
from wagtail.wagtailcore import blocks
from wagtail.wagtailcore.fields import StreamField, RichTextField
from wagtail.wagtailcore.models import Orderable, Page
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailsnippets.models import register_snippet
from wagtail.contrib.settings.models import BaseSetting, register_setting


class LinkFields(models.Model):
    """
    Adds fields for internal and external links with some methods to simplify the rendering:

    <a href="{{ obj.get_link_url }}">{{ obj.get_link_text }}</a>
    """

    link_page = models.ForeignKey(
        'wagtailcore.FieldPanelPage',
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )
    link_url = models.URLField(blank=True)
    link_text = models.CharField(blank=True, max_length=255)

    class Meta:
        abstract = True

    def clean(self):
        if not self.link_page and not self.link_url:
            raise ValidationError({
                'link_url': ValidationError("You must specify link page or link url."),
                'link_page': ValidationError("You must specify link page or link url."),
            })

        if self.link_page and self.link_url:
            raise ValidationError({
                'link_url': ValidationError("You must specify link page or link url. You can't use both."),
                'link_page': ValidationError("You must specify link page or link url. You can't use both."),
            })

        if not self.link_page and not self.link_text:
            raise ValidationError({
                'link_text': ValidationError("You must specify link text, if you use the link url field."),
            })

    def get_link_text(self):
        if self.link_text:
            return self.link_text

        if self.link_page:
            return self.link_page.title

        return ''

    def get_link_url(self):
        if self.link_page:
            return self.link_page.get_url

        return self.link_url

    panels = [
        MultiFieldPanel([
            PageChooserPanel('link_page'),
            FieldPanel('link_url'),
            FieldPanel('link_text'),
        ], 'Link'),
    ]


# Related pages
class RelatedPage(Orderable, models.Model):
    page = models.ForeignKey('wagtailcore.Page', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    class Meta:
        abstract = True
        ordering = ['sort_order']

    panels = [
        PageChooserPanel('page'),
    ]


# Generic social fields abstract class to add social image/text to any new content type easily.
class SocialFields(models.Model):
    social_image = models.ForeignKey('images.CustomImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    social_text = models.CharField(max_length=255, blank=True)

    class Meta:
        abstract = True

    promote_panels = [
        MultiFieldPanel([
            ImageChooserPanel('social_image'),
            FieldPanel('social_text'),
        ], 'Social networks'),
    ]


# Generic listing fields abstract class to add listing image/text to any new content type easily.
class ListingFields(models.Model):
    listing_image = models.ForeignKey(
        'images.CustomImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Choose the image you wish to be displayed when this page appears in listings"
    )
    listing_title = models.CharField(max_length=255, blank=True, help_text="Override the page title used when this page appears in listings")
    listing_summary = models.CharField(max_length=255, blank=True, help_text="The text summary used when this page appears in listings. It's also used as the description for search engines if the 'Search description' field above is not defined.")

    class Meta:
        abstract = True

    promote_panels = [
        MultiFieldPanel([
            ImageChooserPanel('listing_image'),
            FieldPanel('listing_title'),
            FieldPanel('listing_summary'),
        ], 'Listing information'),
    ]


@register_snippet
class CallToActionSnippet(models.Model):
    title = models.CharField(max_length=255)
    summary = RichTextField(blank=True, max_length=255)
    image = models.ForeignKey('images.CustomImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    link = StreamField(
        blocks.StreamBlock([
            (
                'external_link', blocks.StructBlock([
                    ('url', blocks.URLBlock()),
                    ('title', blocks.CharBlock()),
                ], icon='link')
            ),
            (
                'internal_link', blocks.StructBlock([
                    ('page', blocks.PageChooserBlock()),
                    ('title', blocks.CharBlock(required=False)),
                ], icon='link'),
            ),
        ], max_num=1, required=True),
        blank=True
    )

    panels = [
        FieldPanel('title'),
        FieldPanel('summary'),
        ImageChooserPanel('image'),
        StreamFieldPanel('link'),
    ]

    def get_link_text(self):
        # Link is required, so we should always have
        # an element with index 0
        block = self.link[0]

        title = block.value['title']
        if block.block_type == 'external_link':
            return title

        # Title is optional for internal_link
        # so fallback to page's title, if it's empty
        return title or block.value['page'].title

    def get_link_url(self):
        # Link is required, so we should always have
        # an element with index 0
        block = self.link[0]

        if block.block_type == 'external_link':
            return block.value['url']

        return block.value['page'].get_url()

    def __str__(self):
        return self.title


@register_setting
class SocialMediaSettings(BaseSetting):
    twitter_handle = models.CharField(
        max_length=255,
        blank=True,
        help_text='Your Twitter username without the @, e.g. katyperry',
    )
    facebook_app_id = models.CharField(
        max_length=255,
        blank=True,
        help_text='Your Facebook app ID.',
    )
    default_sharing_text = models.CharField(
        max_length=255,
        blank=True,
        help_text='Default sharing text to use if social text has not been set on a page.',
    )
    site_name = models.CharField(
        max_length=255,
        blank=True,
        default='opentech',
        help_text='Site name, used by Open Graph.',
    )


@register_setting
class SystemMessagesSettings(BaseSetting):
    class Meta:
        verbose_name = 'system messages'

    title_404 = models.CharField(
        "Title",
        max_length=255,
        default='Page not found',
    )
    body_404 = RichTextField(
        "Text",
        default='<p>You may be trying to find a page that doesn&rsquo;t exist or has been moved.</p>'
    )

    panels = [
        MultiFieldPanel([
            FieldPanel('title_404'),
            FieldPanel('body_404'),
        ], '404 page'),
    ]


class BasePage(SocialFields, ListingFields, Page):
    show_in_menus_default = True

    header_image = models.ForeignKey(
        'images.CustomImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    class Meta:
        abstract = True

    content_panels = Page.content_panels + [
        ImageChooserPanel('header_image')
    ]

    promote_panels = (
        Page.promote_panels +
        SocialFields.promote_panels +
        ListingFields.promote_panels
    )


class BaseFunding(Orderable):
    value = models.PositiveIntegerField()
    year = models.PositiveIntegerField()
    duration = models.PositiveIntegerField(help_text='In months')
    source = models.ForeignKey(
        'wagtailcore.Page',
        on_delete=models.PROTECT,
    )

    panels = [
        FieldRowPanel([
            FieldPanel('year'),
            FieldPanel('value'),
            FieldPanel('duration'),
        ]),
        PageChooserPanel('source', ['public_funds.FundPage', 'public_funds.LabPage']),
    ]

    class Meta(Orderable.Meta):
        abstract = True


class FundingMixin(models.Model):
    '''Impliments the funding total calulation

    You still need to include the InlinePanel('funding') in the child class
    '''

    class Meta:
        abstract = True

    @property
    def total_funding(self):
        return sum(funding.value for funding in self.funding.all())
