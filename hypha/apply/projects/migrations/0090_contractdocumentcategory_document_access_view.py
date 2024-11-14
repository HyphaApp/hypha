# Generated by Django 4.2.16 on 2024-11-01 16:27

from django.db import migrations, models
from hypha.apply.users.roles import ROLES_ORG_FACULTY


def allow_internal_groups_to_contractdocumentcategory(apps, schema_editor):
    ContractDocumentCategory = apps.get_model(
        "application_projects", "ContractDocumentCategory"
    )
    Group = apps.get_model("auth", "Group")

    groups = Group.objects.filter(name__in=ROLES_ORG_FACULTY)
    for category in ContractDocumentCategory.objects.all():
        # Add the default groups to the document_access_view field
        category.document_access_view.add(*groups)


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("application_projects", "0089_projectreminderfrequency"),
    ]

    operations = [
        migrations.AddField(
            model_name="contractdocumentcategory",
            name="document_access_view",
            field=models.ManyToManyField(
                blank=True,
                help_text="Only selected group's users can access the document",
                limit_choices_to={
                    "name__in": ["Staff", "Staff Admin", "Finance", "Contracting"]
                },
                related_name="contract_document_category",
                to="auth.group",
                verbose_name="Allow document access for groups",
            ),
        ),
        migrations.RunPython(allow_internal_groups_to_contractdocumentcategory),
    ]
