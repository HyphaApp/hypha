from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("funds", "0139_alter_applicationbasedeterminationform_options_and_more"),
    ]

    operations = [
        # Submissions from before search_document was added (0111) were never
        # indexed. Backfill them from search_data before dropping it. Weights are
        # approximate (all "B"); a resave rebuilds the full weighted vector.
        migrations.RunSQL(
            sql="""
                UPDATE funds_applicationsubmission
                SET search_document = setweight(to_tsvector(search_data), 'B')
                WHERE search_document IS NULL
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RemoveField(
            model_name="applicationsubmission",
            name="search_data",
        ),
    ]
