import argparse
import json

from datetime import datetime, timezone

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.utils import IntegrityError

from wagtail.admin.rich_text.converters.editor_html import EditorHTMLConverter
from wagtail.core.rich_text import RichText

from opentech.apply.categories.models import Category, Option
from opentech.apply.categories.categories_seed import CATEGORIES
from opentech.apply.users.models import User
from opentech.public.people.models import PersonPage
from opentech.public.projects.models import ProjectPage
from opentech.public.news.models import (
    NewsIndex,
    NewsPage,
    NewsPageAuthor,
    NewsType,
    NewsPageNewsType,
    NewsProjectRelatedPage,
)


class Command(BaseCommand):
    help = "News migration script. Requires a source JSON file."
    data = []
    terms = {}
    whitelister = EditorHTMLConverter().whitelister

    def add_arguments(self, parser):
        parser.add_argument('source', type=argparse.FileType('r'), help='Migration source JSON file')

    @transaction.atomic
    def handle(self, *args, **options):
        # Prepare the list of categories.
        for item in CATEGORIES:
            category, _ = Category.objects.get_or_create(name=item['category'])
            option, _ = Option.objects.get_or_create(value=item['name'], category=category)
            self.terms[item['tid']] = option

        self.parent_page = NewsIndex.objects.first()

        if not self.parent_page:
            raise NewsIndex.DoesNotExist('News Index Page must exist to import News')

        self.types = {
            '4': NewsType.objects.get_or_create(title='Press Clip')[0],
            '5': NewsType.objects.get_or_create(title='Program Update')[0],
            '388': NewsType.objects.get_or_create(title='Research')[0],
        }

        with options['source'] as json_data:
            self.data = json.load(json_data)

            counter = 0
            for id in self.data:
                self.process(id)
                counter += 1

            self.stdout.write(f"Imported {counter} submissions.")

    def process(self, id):
        node = self.data[id]

        try:
            news = NewsPage.objects.get(drupal_id=node['nid'])
        except NewsPage.DoesNotExist:
            news = NewsPage(drupal_id=node['nid'])

        # TODO timezone?
        news.submit_time = datetime.fromtimestamp(int(node['created']), timezone.utc)
        news.publication_date = datetime.fromtimestamp(int(node['created']), timezone.utc)
        print(news.publication_date)

        news.title = node['title']

        news.introduction = self.get_field(node, 'field_preamble')

        cleaned_body = self.whitelister.clean(self.get_field(node, 'body'))
        news.body = [('paragraph', RichText(cleaned_body))]

        news.news_types.clear()
        for news_type in self.ensure_iterable(node['field_article_type']):
            news.news_types.add(NewsPageNewsType(
                news_type=self.types[news_type['tid']],
            ))

        news.related_projects.clear()
        for project in self.ensure_iterable(node['field_article_project']):
            try:
                project_page = ProjectPage.objects.get(drupal_id=project['target_id'])
            except ProjectPage.DoesNotExist:
                self.stdout.write(f"Missing project ID {project['target_id']}")
            else:
                news.related_projects.add(NewsProjectRelatedPage(
                    page=project_page,
                ))

        news.authors.clear()
        for author in self.ensure_iterable(node['field_article_authors']):
            user = User.objects.get(drupal_id=author['target_id'])
            news.authors.add(NewsPageAuthor(
                author=PersonPage.objects.get(title=user.full_name)
            ))

        try:
            user = User.objects.get(drupal_id=node['uid'])
        except User.DoesNotExist:
            pass
        else:
            user_map = {'Dan Blah': 'Dan "Blah" Meredith'}
            name = user_map.get(user.full_name, user.full_name)
            # missing amin jobran
            try:
                news.authors.add(NewsPageAuthor(
                    author=PersonPage.objects.get(title=name)
                ))
            except PersonPage.DoesNotExist:
                print(f'missing person page: {name}')

        try:
            if not news.get_parent():
                self.parent_page.add_child(instance=news)
            news.save_revision().publish()
            self.stdout.write(f"Processed \"{node['title'].encode('utf8')}\" ({node['nid']})")
        except IntegrityError:
            self.stdout.write(f"*** Skipped \"{node['title']}\" ({node['nid']}) due to IntegrityError")

    def ensure_iterable(self, value):
        if isinstance(value, dict):
            value = [value]
        return value

    def get_field(self, node, field):
        try:
            return node[field]['safe_value']
        except TypeError:
            pass
        try:
            return node[field]['value']
        except TypeError:
            return ''
