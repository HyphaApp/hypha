# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-01-05 17:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):
    dependencies = [
        ("people", "0002_add_header_image"),
    ]

    operations = [
        migrations.CreateModel(
            name="PersonContactInfomation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "sort_order",
                    models.IntegerField(blank=True, editable=False, null=True),
                ),
                (
                    "contact_method",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("irc", "IRC"),
                            ("im_jabber_xmpp", "IM/Jabber/XMPP"),
                            ("phone", "Phone"),
                            ("pgp", "PGP fingerprint"),
                            ("otr", "OTR fingerprint"),
                        ],
                        max_length=255,
                    ),
                ),
                (
                    "other_method",
                    models.CharField(blank=True, max_length=255, verbose_name="Other"),
                ),
                ("contact_detail", models.CharField(max_length=255)),
                (
                    "page",
                    modelcluster.fields.ParentalKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contact_details",
                        to="people.PersonPage",
                    ),
                ),
            ],
            options={
                "ordering": ["sort_order"],
                "abstract": False,
            },
        ),
        migrations.RemoveField(
            model_name="personpagephonenumber",
            name="page",
        ),
        migrations.DeleteModel(
            name="PersonPagePhoneNumber",
        ),
    ]
