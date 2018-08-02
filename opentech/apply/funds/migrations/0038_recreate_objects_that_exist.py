# Generated by Django 2.0.2 on 2018-08-02 09:13

from django.db import migrations


def recreate_objects(apps, schema_editor):
    # We removed the old definition of these objects, need to create
    # a new object with a pointer back to that object, the underlying
    # data structure was unaffected
    ContentType = apps.get_model('contenttypes.ContentType')


    for model_name, new_model_name in [
            ('FundType', 'ApplicationBase'),
            ('LabType', 'LabBase'),
            ('Round', 'RoundBase'),
    ]:
        content_type, _ = ContentType.objects.get_or_create(model=model_name.lower(), app_label='funds')

        model = apps.get_model('funds', model_name)
        new_model = apps.get_model('funds', new_model_name)
        for obj in new_model.objects.all():
            kwargs = {
                f'{new_model_name.lower()}_ptr': obj,
                'title': obj.title,
                'draft_title': obj.draft_title,
                'slug': obj.slug,
                'content_type': content_type,
                'path': obj.path,
                'depth': obj.depth,
                'numchild': obj.numchild,
                'url_path': obj.url_path,
            }
            try:
                kwargs.update(lead=obj.lead)
            except:
                pass

            new_obj = model(**kwargs)
            new_obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('funds', '0037_refactor_funds_models'),
    ]

    operations = [
        migrations.RunPython(recreate_objects, migrations.RunPython.noop),
    ]
