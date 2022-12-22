# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-04-14 09:29
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields
import wagtail.blocks
import wagtail.fields
import wagtail.documents.blocks
import wagtail.embeds.blocks
import wagtail.images.blocks
import wagtail.snippets.blocks


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('wagtailcore', '0032_add_bulk_delete_page_permission'),
        ('images', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PersonType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
            ]
        ),
        migrations.CreateModel(
            name='PersonIndexPage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('social_image', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='images.CustomImage')),
                ('social_text', models.CharField(blank=True, max_length=255)),
                ('listing_image', models.ForeignKey(blank=True, help_text='Choose the image you wish to be displayed when this page appears in listings', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='images.CustomImage')),
                ('listing_summary', models.CharField(blank=True, help_text="The text summary used when this page appears in listings. It's also used as the description for search engines if the 'Search description' field above is not defined.", max_length=255)),
                ('listing_title', models.CharField(blank=True, help_text='Override the page title used when this page appears in listings', max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='PersonPage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('first_name', models.CharField(max_length=255)),
                ('last_name', models.CharField(max_length=255)),
                ('job_title', models.CharField(max_length=255)),
                ('introduction', models.TextField(blank=True)),
                ('website', models.URLField(blank=True, max_length=255)),
                ('biography', wagtail.fields.StreamField((('heading', wagtail.blocks.CharBlock(classname='full title', icon='title')), ('paragraph', wagtail.blocks.RichTextBlock()), ('image', wagtail.blocks.StructBlock((('image', wagtail.images.blocks.ImageChooserBlock()), ('caption', wagtail.blocks.CharBlock(required=False))))), ('quote', wagtail.blocks.StructBlock((('quote', wagtail.blocks.CharBlock(classname='title')), ('attribution', wagtail.blocks.CharBlock(required=False)), ('job_title', wagtail.blocks.CharBlock(required=False))))), ('embed', wagtail.embeds.blocks.EmbedBlock()), ('call_to_action', wagtail.snippets.blocks.SnippetChooserBlock('utils.CallToActionSnippet', template='blocks/call_to_action_block.html')), ('document', wagtail.blocks.StructBlock((('document', wagtail.documents.blocks.DocumentChooserBlock()), ('title', wagtail.blocks.CharBlock(required=False)))))), blank=True)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('mobile_phone', models.CharField(blank=True, max_length=255)),
                ('landline_phone', models.CharField(blank=True, max_length=255)),
                ('photo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='images.CustomImage')),
                ('social_image', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='images.CustomImage')),
                ('social_text', models.CharField(blank=True, max_length=255)),
                ('listing_image', models.ForeignKey(blank=True, help_text='Choose the image you wish to be displayed when this page appears in listings', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='images.CustomImage')),
                ('listing_summary', models.CharField(blank=True, help_text="The text summary used when this page appears in listings. It's also used as the description for search engines if the 'Search description' field above is not defined.", max_length=255)),
                ('listing_title', models.CharField(blank=True, help_text='Override the page title used when this page appears in listings', max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='PersonPagePersonType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('person_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='people.PersonType')),
                ('page', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='person_types', to='people.PersonPage')),
            ],
        ),
        migrations.CreateModel(
            name='SocialMediaProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('service', models.CharField(choices=[('twitter', 'Twitter'), ('linkedin', 'LinkedIn')], max_length=200)),
                ('username', models.CharField(max_length=255)),
                ('person_page', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='social_media_profile', to='people.PersonPage')),
            ],
        ),
        migrations.CreateModel(
            name='PersonPagePhoneNumber',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(max_length=255)),
                ('page', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='phone_numbers', to='people.PersonPage')),
            ],
        ),
        migrations.RemoveField(
            model_name='personpage',
            name='landline_phone',
        ),
        migrations.RemoveField(
            model_name='personpage',
            name='mobile_phone',
        ),
    ]
