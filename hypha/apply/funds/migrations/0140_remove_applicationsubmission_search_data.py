from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("funds", "0139_alter_applicationbasedeterminationform_options_and_more"),
    ]

    operations = [
        # Submissions from before search_document was added (0111) were never
        # indexed. Backfill them from search_data before dropping it. Weights are
        # approximate (all "B"); run the rebuild_search_index management command
        # afterwards to rebuild the full weighted vector for every submission.
        migrations.RunSQL(
            sql="""
                UPDATE funds_applicationsubmission
                SET search_document = setweight(to_tsvector(search_data), 'B')
                WHERE search_document IS NULL
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        # Give the field a default so that reversing the RemoveField can re-add
        # the NOT NULL column to a table with existing rows.
        migrations.AlterField(
            model_name="applicationsubmission",
            name="search_data",
            field=models.TextField(default=""),
        ),
        migrations.RemoveField(
            model_name="applicationsubmission",
            name="search_data",
        ),
    ]
