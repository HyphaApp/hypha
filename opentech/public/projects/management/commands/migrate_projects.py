import argparse
import itertools
import json
import mimetypes

from datetime import datetime, timezone
from urllib.parse import urlsplit
from io import BytesIO

import requests
from PIL import Image

import bleach
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.utils import IntegrityError

from wagtail.admin.rich_text.converters.editor_html import EditorHTMLConverter
from wagtail.core.models import Page
from wagtail.core.rich_text import RichText
from wagtail.images import get_image_model

from opentech.apply.categories.models import Category, Option
from opentech.apply.categories.categories_seed import CATEGORIES
from opentech.public.projects.models import (
    ProjectContactDetails,
    ProjectFunding,
    ProjectIndexPage,
    ProjectPage,
)


WagtailImage = get_image_model()

VALID_IMAGE_EXTENSIONS = [
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
]

VALID_IMAGE_MIMETYPES = [
    "image"
]


def valid_url_extension(url, extension_list=VALID_IMAGE_EXTENSIONS):
    return any([url.endswith(e) for e in extension_list])


def valid_url_mimetype(url, mimetype_list=VALID_IMAGE_MIMETYPES):
    mimetype, encoding = mimetypes.guess_type(url)
    if mimetype:
        return any([mimetype.startswith(m) for m in mimetype_list])
    else:
        return False


class Command(BaseCommand):
    help = "Project migration script. Requires a source JSON file."
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

        self.parent_page = ProjectIndexPage.objects.first()

        if not self.parent_page:
            raise ProjectIndexPage.DoesNotExist('Project Index Page must exist to import projects')

        self.funds = {
            '3625': Page.objects.get(title='Internet Freedom Fund'),
            '3654': Page.objects.get(title='Rapid Response Fund'),
            '3905': Page.objects.get(title='Core Infrastructure Fund'),
            '7791': Page.objects.get(title='Community Lab'),
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
            project = ProjectPage.objects.get(drupal_id=node['nid'])
        except ProjectPage.DoesNotExist:
            project = ProjectPage(drupal_id=node['nid'])

        # TODO timezone?
        project.submit_time = datetime.fromtimestamp(int(node['created']), timezone.utc)

        project.title = node['title']

        image_url_base = 'https://www.opentech.fund/sites/default/files/'
        try:
            uri = node['field_project_image']['uri']
        except TypeError:
            # There was no image
            pass
        else:
            parts = urlsplit(uri)
            image_url = image_url_base + parts.netloc + parts.path
            project.icon = self.wagtail_image_obj_from_url(image_url, node['field_project_image']['fid'])

        project.introduction = self.get_field(node, 'field_preamble')

        cleaned_body = self.whitelister.clean(self.get_field(node, 'body'))
        if project.introduction:
            project.body = [('paragraph', RichText(cleaned_body))]
        else:
            # Use the first sentence of the body as an intro
            very_clean_body = bleach.clean(cleaned_body, strip=True)
            introduction = very_clean_body.split('.')[0] + '.'
            project.introduction = introduction
            body_without_intro = cleaned_body.replace(introduction, '').strip()
            project.body = [('paragraph', RichText(body_without_intro))]

        status = {
            '329': 'idea',
            '328': 'exists',
            '366': 'release',
            '367': 'production',
        }
        project.status = status[node['field_proposal_status']['tid']]

        project.contact_details.clear()

        sites = node['field_project_url']

        if isinstance(sites, dict):
            sites = [sites]

        for site in sites:
            url = site['url']
            if 'github' in url:
                page_type = 'github'
                url = urlsplit(url).path
            else:
                page_type = 'website'

            project.contact_details.add(ProjectContactDetails(
                service=page_type,
                value=url,
            ))

        project.contact_details.add(ProjectContactDetails(
            service='twitter',
            value=self.get_field(node, 'field_project_twitter')
        ))

        # Funding
        project.funding.clear()

        years = self.ensure_iterable(node['field_project_funding_year'])
        amounts = self.ensure_iterable(node['field_project_funding_amount'])
        durations = self.ensure_iterable(node['field_project_term_time'])
        funds = self.ensure_iterable(node['field_project_funding_request'])
        for year, amount, duration, fund in itertools.zip_longest(years, amounts, durations, funds):
            try:
                fund = self.funds[fund['target_id']]
            except TypeError:
                fund = None

            try:
                duration = duration['value']
            except TypeError:
                duration = 0

            try:
                amount = amount['value']
            except TypeError:
                # This is an error, don't give funding
                continue

            project.funding.add(ProjectFunding(
                value=amount,
                year=year['value'],
                duration=duration,
                source=fund,
            ))

        try:
            if not project.get_parent():
                self.parent_page.add_child(instance=project)
            project.save_revision().publish()
            self.stdout.write(f"Processed \"{node['title'].encode('utf8')}\" ({node['nid']})")
        except IntegrityError:
            self.stdout.write(f"*** Skipped \"{node['title']}\" ({node['nid']}) due to IntegrityError")
            pass

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

    def get_referenced_term(self, tid):
        try:
            term = self.terms[tid]
            return term.id
        except KeyError:
            return None

    def nl2br(self, value):
        return value.replace('\r\n', '<br>\n')

    @staticmethod
    def wagtail_image_obj_from_url(url, drupal_id=None):
        """
        Get the image from the Nesta site if it doesn't already exist.
        """

        if drupal_id is not None and drupal_id:
            try:
                return WagtailImage.objects.get(drupal_id=drupal_id)
            except WagtailImage.DoesNotExist:
                pass

        if url and valid_url_extension(url) and valid_url_mimetype(url):
            r = requests.get(url, stream=True)

            if r.status_code == requests.codes.ok:
                img_buffer = BytesIO(r.content)
                img_filename = url.rsplit('/', 1)[1]

                # Test downloaded file is valid image file
                try:
                    pil_image = Image.open(img_buffer)
                    pil_image.verify()
                except Exception as e:
                    print(f"Invalid image {url}: {e}")
                else:
                    img = WagtailImage.objects.create(
                        title=img_filename,
                        file=ImageFile(img_buffer, name=img_filename),
                        drupal_id=drupal_id
                    )
                    return img
        return None
