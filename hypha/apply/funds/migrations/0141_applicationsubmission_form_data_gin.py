import django.contrib.postgres.indexes
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations


class Migration(migrations.Migration):
    # Concurrent index creation can't run inside a transaction.
    atomic = False

    dependencies = [
        ("funds", "0140_remove_applicationsubmission_search_data"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="applicationsubmission",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["form_data"],
                name="funds_appsub_form_data_gin",
                opclasses=["jsonb_path_ops"],
            ),
        ),
    ]
