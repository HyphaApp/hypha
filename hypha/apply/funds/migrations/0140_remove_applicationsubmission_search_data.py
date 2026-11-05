from django.core.management import call_command
from django.db import migrations, models


def rebuild_search_index(apps, schema_editor):
    # Nothing to index on a new install, and that way only sites upgrading
    # through this migration depend on the current model code.
    if not apps.get_model("funds", "ApplicationSubmission").objects.exists():
        return

    # Submissions from before search_document was added (0111) were never
    # indexed, and older indexed ones may have "id:None" instead of their
    # public id. Rebuild the full weighted vector for every submission before
    # dropping search_data. Uses the real model, but the command only loads
    # columns that exist at this point. Submissions that can't be indexed
    # (e.g. over the tsvector size limit) are reported and skipped.
    call_command("rebuild_search_index")


class Migration(migrations.Migration):
    # Let the rebuild commit chunk by chunk instead of holding row locks on
    # every submission in one long transaction.
    atomic = False

    dependencies = [
        # Loading form fields queries the categories tables.
        ("categories", "0009_alter_option_options"),
        ("funds", "0139_alter_applicationbasedeterminationform_options_and_more"),
    ]

    operations = [
        migrations.RunPython(rebuild_search_index, migrations.RunPython.noop),
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
