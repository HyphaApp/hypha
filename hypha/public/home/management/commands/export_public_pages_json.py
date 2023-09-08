import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from hypha.public.news.models import NewsPage
from hypha.public.people.models import PersonPage
from hypha.public.projects.models import ProjectPage


class Command(BaseCommand):
    help = "Export public pages to json files."

    def get_streamfield_as_blocks(self, field):
        streamfields = []
        for block in field:
            if hasattr(block.value, "render_as_block"):
                streamfields.append(str(block.value.render_as_block()))
            else:
                streamfields.append(str(block.value))
        body = "".join(streamfields)
        return body

    def get_authors(self, items):
        related = []
        for item in items.all():
            related.append(item.author.slug)
        return ",".join(related)

    def get_related_pages(self, items):
        related = []
        for item in items.all():
            related.append(item.source_page.slug)
        return ",".join(related)

    def get_types(self, items):
        related = []
        for item in items.all():
            try:
                related.append(item.news_type.title)
            except AttributeError:
                related.append(item.person_type.title)
        return ",".join(related)

    def get_funding(self, items):
        funding = []
        for item in items.all():
            funding.append(
                {
                    "year": str(item.year),
                    "duration": str(item.duration),
                    "value": int(item.value),
                    "source": str(item.source).strip(),
                }
            )
        return funding

    def get_contact(self, items):
        contact = []
        for item in items.all():
            contact.append(
                {
                    "url": str(item.url),
                    "service": str(item.service),
                }
            )
        return contact

    def get_image(self, item):
        try:
            return item.file.path.replace(
                f"{settings.BASE_DIR}/media/original_images/", ""
            )
        except AttributeError:
            pass

    def handle(self, *args, **options):
        try:
            os.mkdir("exports")
        except FileExistsError:
            pass

        # News export
        newsdata = []
        for page in NewsPage.objects.live().public():
            newsdata.append(
                {
                    "oldid": int(page.id),
                    "title": str(page.title).strip(),
                    "date": str(page.first_published_at.isoformat()),
                    "lastmod": str(page.latest_revision_created_at.isoformat()),
                    "authors": self.get_authors(page.authors),
                    "types": self.get_types(page.news_types),
                    "related_pages": self.get_related_pages(page.related_pages),
                    "related_projects": self.get_related_pages(page.related_projects),
                    "intro": str(page.introduction).strip(),
                    "body": self.get_streamfield_as_blocks(page.body),
                    "slug": str(page.slug).strip(),
                }
            )
            with open("exports/news.json", "w", newline="") as jsonfile:
                json.dump(newsdata, jsonfile)

        # People export
        peopledata = []
        for page in PersonPage.objects.live().public():
            peopledata.append(
                {
                    "oldid": int(page.id),
                    "title": str(page.title).strip(),
                    "date": str(page.first_published_at.isoformat()),
                    "lastmod": str(page.latest_revision_created_at.isoformat()),
                    "active": bool(page.active),
                    "photo": self.get_image(page.photo),
                    "jobtitle": str(page.title).strip(),
                    "types": self.get_types(page.person_types),
                    "email": str(page.email).strip(),
                    "web": str(page.website).strip(),
                    "intro": str(page.introduction).strip(),
                    "body": self.get_streamfield_as_blocks(page.biography),
                    "slug": str(page.slug).strip(),
                }
            )
            with open("exports/people.json", "w", newline="") as jsonfile:
                json.dump(peopledata, jsonfile)

        # Project export
        projectdata = []
        for page in ProjectPage.objects.live().public():
            projectdata.append(
                {
                    "oldid": int(page.id),
                    "title": str(page.title).strip(),
                    "date": str(page.first_published_at.isoformat()),
                    "icon": self.get_image(page.icon),
                    "lastmod": str(page.latest_revision_created_at.isoformat()),
                    "funding": self.get_funding(page.funding),
                    "contact": self.get_contact(page.contact_details),
                    "related_pages": self.get_related_pages(page.related_pages),
                    "intro": str(page.introduction).strip(),
                    "body": self.get_streamfield_as_blocks(page.body),
                    "slug": str(page.slug).strip(),
                }
            )
            with open("exports/projects.json", "w", newline="") as jsonfile:
                json.dump(projectdata, jsonfile)
