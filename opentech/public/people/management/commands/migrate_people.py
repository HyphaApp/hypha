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
from opentech.public.people.models import (
    Funding,
    FundReviewers,
    PersonContactInfomation,
    PersonPage,
    PersonIndexPage,
    PersonType,
    PersonPagePersonType,
    SocialMediaProfile,
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
    help = "Person migration script. Requires a source JSON file."
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

        self.parent_page = PersonIndexPage.objects.first()

        if not self.parent_page:
            raise PersonIndexPage.DoesNotExist('Project Index Page must exist to import projects')

        self.types = {
            'team': PersonType.objects.get_or_create(title='Team')[0],
            'council': PersonType.objects.get_or_create(title='Advisory Council')[0],
            'fellow': PersonType.objects.get_or_create(title='Fellow')[0],
        }

        self.funds = {
            '3625': Page.objects.get(title='Internet Freedom Fund'),
            '3654': Page.objects.get(title='Rapid Response Fund'),
            '3905': Page.objects.get(title='Core Infrastructure Fund'),
            '7791': Page.objects.get(title='Community Lab'),
            '3618': Page.objects.get(title='Information Controls Fellowship'),
            '3613': None,
            '3681': Page.objects.get(title='Digital Integrity Fellowship'),
        }

        self.review_funds = {
            '393': Page.objects.get(title='Internet Freedom Fund'),
            '389': Page.objects.get(title='Rapid Response Fund'),
            '391': Page.objects.get(title='Core Infrastructure Fund'),
            'NOT_USED': Page.objects.get(title='Community Lab'),
            '394': Page.objects.get(title='Information Controls Fellowship'),
            '390': Page.objects.get(title='Digital Integrity Fellowship'),
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
        print(node['title'].encode('utf8'))

        try:
            person = PersonPage.objects.get(drupal_id=node['nid'])
        except PersonPage.DoesNotExist:
            person = PersonPage(drupal_id=node['nid'])

        # TODO timezone?
        person.submit_time = datetime.fromtimestamp(int(node['created']), timezone.utc)

        *first_name, last_name = node['title'].split()

        person.first_name = ' '.join(first_name)
        person.last_name = last_name

        person.title = node['title']

        person.job_title = self.get_field(node, 'field_team_title')

        person.active = bool(int(node['field_team_status']['value']))

        person.person_types.clear()
        for person_type in self.ensure_iterable(node['field_team_type']):
            person.person_types.add(PersonPagePersonType(
                person_type=self.types[person_type['value']],
            ))

        image_url_base = 'https://www.opentech.fund/sites/default/files/'

        try:
            uri = node['field_team_photo']['uri']
        except TypeError:
            # There was no image
            pass
        else:
            parts = urlsplit(uri)
            image_url = image_url_base + parts.netloc + parts.path
            person.photo = self.wagtail_image_obj_from_url(image_url, node['field_team_photo']['fid'])

        cleaned_body = self.whitelister.clean(self.get_field(node, 'body'))

        # Use the first sentence of the body as an intro
        very_clean_body = bleach.clean(cleaned_body, strip=True)
        very_clean_body = very_clean_body.replace('.\n', '. ')
        parts = very_clean_body.split('. ')
        introduction = ''
        while len(introduction) < 20:
            try:
                introduction += parts.pop(0)
                introduction += '. '
            except IndexError:
                break

        introduction = introduction.strip()
        person.introduction = introduction
        body_without_intro = cleaned_body.replace(introduction, '').strip()
        person.biography = [('paragraph', RichText(body_without_intro))]

        person.social_media_profile.clear()

        if self.get_field(node, 'field_team_twitter'):
            person.social_media_profile.add(SocialMediaProfile(
                service='twitter',
                username=self.get_field(node, 'field_team_twitter')
            ))

        person.contact_details.clear()
        for contact in ['im', 'otr', 'irc', 'pgp', 'phone']:
            if self.get_field(node, f'field_team_{contact}'):
                person.contact_details.add(PersonContactInfomation(
                    contact_method=contact,
                    contact_detail=self.get_field(node, f'field_team_{contact}')
                ))

        person.funds_reviewed.clear()
        for reviewer in self.ensure_iterable(node['field_team_review_panel']):
            person.funds_reviewed.add(FundReviewers(
                page=self.review_funds[reviewer['tid']],
            ))

        # Funding
        person.funding.clear()

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

            person.funding.add(Funding(
                value=amount,
                year=year['value'],
                duration=duration,
                source=fund,
            ))

        try:
            if not person.get_parent():
                self.parent_page.add_child(instance=person)
            person.save_revision().publish()
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
            return self.terms[tid]
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
