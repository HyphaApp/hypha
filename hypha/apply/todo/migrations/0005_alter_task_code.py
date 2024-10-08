# Generated by Django 4.2.11 on 2024-08-21 13:01

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("todo", "0004_alter_task_code"),
    ]

    operations = [
        migrations.AlterField(
            model_name="task",
            name="code",
            field=models.CharField(
                choices=[
                    ("submission_draft", "Submission Draft"),
                    ("determination_draft", "Determination draft"),
                    ("review_draft", "Review Draft"),
                    ("project_waiting_paf", "Project waiting project form"),
                    ("project_submit_paf", "Project submit project form"),
                    ("paf_required_changes", "Project form required changes"),
                    ("paf_waiting_assignee", "Project form waiting assignee"),
                    ("paf_waiting_approval", "Project form waiting approval"),
                    ("project_waiting_contract", "Project waiting contract"),
                    (
                        "project_waiting_contract_document",
                        "Project waiting contract document",
                    ),
                    (
                        "project_waiting_contract_review",
                        "Project waiting contract review",
                    ),
                    ("project_waiting_invoice", "Project waiting invoice"),
                    ("invoice_required_changes", "Invoice required changes"),
                    ("invoice_waiting_approval", "Invoice waiting approval"),
                    ("invoice_waiting_paid", "Invoice waiting paid"),
                    ("report_due", "Report due"),
                ],
                max_length=50,
            ),
        ),
    ]
