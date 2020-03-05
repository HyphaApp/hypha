# Generated by Django 2.2.9 on 2020-03-02 11:31

from django.db import migrations
import wagtail.core.blocks
import wagtail.core.fields
import wagtail.embeds.blocks
import wagtail.images.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('reset_network_resources', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resetnetworkresourcepage',
            name='content_text',
            field=wagtail.core.fields.StreamField([('text', wagtail.core.blocks.RichTextBlock()), ('image', wagtail.images.blocks.ImageChooserBlock()), ('embed', wagtail.embeds.blocks.EmbedBlock())]),
        ),
    ]
