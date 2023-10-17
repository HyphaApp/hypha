# Generated by Django 2.0.13 on 2019-08-26 12:04

from decimal import Decimal
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("application_projects", "0020_rename_value_to_requested_value"),
    ]

    operations = [
        migrations.AddField(
            model_name="paymentrequest",
            name="paid_value",
            field=models.DecimalField(
                decimal_places=2,
                max_digits=10,
                null=True,
                validators=[django.core.validators.MinValueValidator(Decimal("0.01"))],
            ),
        ),
    ]
