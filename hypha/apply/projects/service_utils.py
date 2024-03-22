from django.conf import settings
from django.contrib.auth.models import Group

from hypha.apply.todo.options import (
    INVOICE_REQUIRED_CHANGES,
    INVOICE_WAITING_APPROVAL,
    INVOICE_WAITING_PAID,
)
from hypha.apply.todo.views import (
    add_task_to_user,
    add_task_to_user_group,
    remove_tasks_for_user_group,
)
from hypha.apply.users.groups import (
    APPROVER_GROUP_NAME,
    FINANCE_GROUP_NAME,
    STAFF_GROUP_NAME,
)

from .models.payment import (
    APPROVED_BY_FINANCE,
    APPROVED_BY_FINANCE_2,
    APPROVED_BY_STAFF,
    CHANGES_REQUESTED_BY_FINANCE,
    CHANGES_REQUESTED_BY_FINANCE_2,
    CHANGES_REQUESTED_BY_STAFF,
    RESUBMITTED,
    SUBMITTED,
)


def handle_tasks_on_invoice_update(old_status, invoice):
    if old_status in [SUBMITTED, RESUBMITTED]:
        # remove invoice waiting approval task for staff
        remove_tasks_for_user_group(
            code=INVOICE_WAITING_APPROVAL,
            user_group=Group.objects.filter(name=STAFF_GROUP_NAME),
            related_obj=invoice,
        )
        if invoice.status == CHANGES_REQUESTED_BY_STAFF:
            # add invoice required changes task for applicant
            add_task_to_user(
                code=INVOICE_REQUIRED_CHANGES,
                user=invoice.project.user,
                related_obj=invoice,
            )
        elif invoice.status == APPROVED_BY_STAFF:
            # add invoice waiting approval task for finance group
            add_task_to_user_group(
                code=INVOICE_WAITING_APPROVAL,
                user_group=Group.objects.filter(name=FINANCE_GROUP_NAME),
                related_obj=invoice,
            )
    if old_status == APPROVED_BY_STAFF:
        # remove invoice waiting approval task for finance group
        remove_tasks_for_user_group(
            code=INVOICE_WAITING_APPROVAL,
            user_group=Group.objects.filter(name=FINANCE_GROUP_NAME),
            related_obj=invoice,
        )
        if invoice.status == CHANGES_REQUESTED_BY_FINANCE:
            # add invoice required changes task for staff
            add_task_to_user_group(
                code=INVOICE_REQUIRED_CHANGES,
                user_group=Group.objects.filter(name=STAFF_GROUP_NAME),
                related_obj=invoice,
            )
        elif invoice.status == APPROVED_BY_FINANCE:
            if settings.INVOICE_EXTENDED_WORKFLOW:
                # add invoice waiting approval task for finance2 group
                add_task_to_user_group(
                    code=INVOICE_WAITING_APPROVAL,
                    user_group=Group.objects.filter(name=FINANCE_GROUP_NAME).filter(
                        name=APPROVER_GROUP_NAME
                    ),
                    related_obj=invoice,
                )
            else:
                # add invoice waiting paid task for finance
                add_task_to_user_group(
                    code=INVOICE_WAITING_PAID,
                    user_group=Group.objects.filter(name=FINANCE_GROUP_NAME),
                    related_obj=invoice,
                )
    if old_status == CHANGES_REQUESTED_BY_FINANCE:
        # remove invoice required changes task for staff
        remove_tasks_for_user_group(
            code=INVOICE_REQUIRED_CHANGES,
            user_group=Group.objects.filter(name=STAFF_GROUP_NAME),
            related_obj=invoice,
        )
        if invoice.status == CHANGES_REQUESTED_BY_STAFF:
            # add invoice required changes task for applicant
            add_task_to_user(
                code=INVOICE_REQUIRED_CHANGES,
                user=invoice.project.user,
                related_obj=invoice,
            )
    if not settings.INVOICE_EXTENDED_WORKFLOW and old_status == APPROVED_BY_FINANCE:
        # remove invoice waiting paid task for finance group
        remove_tasks_for_user_group(
            code=INVOICE_WAITING_PAID,
            user_group=Group.objects.filter(name=FINANCE_GROUP_NAME),
            related_obj=invoice,
        )
    if settings.INVOICE_EXTENDED_WORKFLOW:
        if old_status == APPROVED_BY_FINANCE:
            # remove invoice waiting approval task for finance2 group
            remove_tasks_for_user_group(
                code=INVOICE_WAITING_APPROVAL,
                user_group=Group.objects.filter(name=FINANCE_GROUP_NAME).filter(
                    name=APPROVER_GROUP_NAME
                ),
                related_obj=invoice,
            )
            if invoice.status == CHANGES_REQUESTED_BY_FINANCE_2:
                # add invoice required changes task for finance
                add_task_to_user_group(
                    code=INVOICE_REQUIRED_CHANGES,
                    user_group=Group.objects.filter(name=FINANCE_GROUP_NAME),
                    related_obj=invoice,
                )
            elif invoice.status == APPROVED_BY_FINANCE_2:
                # add invoice waiting paid task for finance2
                add_task_to_user_group(
                    code=INVOICE_WAITING_PAID,
                    user_group=Group.objects.filter(name=FINANCE_GROUP_NAME).filter(
                        name=APPROVER_GROUP_NAME
                    ),
                    related_obj=invoice,
                )
        if old_status == CHANGES_REQUESTED_BY_FINANCE_2:
            # remove invoice required changes task for finance
            remove_tasks_for_user_group(
                code=INVOICE_REQUIRED_CHANGES,
                user_group=Group.objects.filter(name=FINANCE_GROUP_NAME),
                related_obj=invoice,
            )
            if invoice.status == CHANGES_REQUESTED_BY_FINANCE:
                # add invoice required changes task for staff
                add_task_to_user_group(
                    code=INVOICE_REQUIRED_CHANGES,
                    user_group=Group.objects.filter(name=STAFF_GROUP_NAME),
                    related_obj=invoice,
                )
        if old_status == APPROVED_BY_FINANCE_2:
            # remove invoice waiting paid task for finance2
            remove_tasks_for_user_group(
                code=INVOICE_WAITING_PAID,
                user_group=Group.objects.filter(name=FINANCE_GROUP_NAME).filter(
                    name=APPROVER_GROUP_NAME
                ),
                related_obj=invoice,
            )


def batch_update_invoices_status(invoices, user, status):
    for invoice in invoices:
        invoice.status = status
        invoice.save(update_fields=["status"])
