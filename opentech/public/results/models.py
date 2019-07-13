from django.db import models

from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, PageChooserPanel, StreamFieldPanel
from wagtail.core.fields import StreamField
from wagtail.search import index

from modelcluster.fields import ParentalKey

from opentech.public.utils.blocks import StoryBlock
from opentech.public.utils.models import BasePage, RelatedPage


class ResultPageRelatedProject(RelatedPage):
    source_page = ParentalKey('ResultPage', related_name='related_projects')

    panels = [
        PageChooserPanel('page', 'projects.ProjectPage'),
    ]


class ResultPageRelatedPeople(RelatedPage):
    source_page = ParentalKey('ResultPage', related_name='related_people')

    panels = [
        PageChooserPanel('page', 'people.PersonPage'),
    ]


class ResultPageRelatedNews(RelatedPage):
    source_page = ParentalKey('ResultPage', related_name='related_news')

    panels = [
        PageChooserPanel('page', 'news.NewsPage'),
    ]


class ResultPageRelatedPages(RelatedPage):
    source_page = ParentalKey('ResultPage', related_name='related_pages')


class ResultPage(BasePage):
    subpage_types = []
    parent_page_types = ['standardpages.IndexPage']

    introduction = models.TextField(blank=True)
    body = StreamField(StoryBlock())

    search_fields = BasePage.search_fields + [
        index.SearchField('introduction'),
        index.SearchField('body'),
    ]

    content_panels = BasePage.content_panels + [
        FieldPanel('introduction'),
        StreamFieldPanel('body'),
        InlinePanel('related_projects', label="Related projects"),
        InlinePanel('related_people', label="Related people"),
        InlinePanel('related_news', label="Related news"),
        InlinePanel('related_pages', label="Related pages"),
    ]
