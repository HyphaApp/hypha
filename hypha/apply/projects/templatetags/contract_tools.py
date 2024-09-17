from django import template
from django.conf import settings

from hypha.apply.projects.models.project import CONTRACTING

from ..permissions import has_permission

register = template.Library()


@register.simple_tag
def user_can_approve_contract(user, project):
    can_approve, _ = has_permission(
        "contract_approve", user, object=project, raise_exception=False
    )
    return can_approve


@register.simple_tag
def is_project_contract_approved(project):
    contract = project.contracts.order_by("-created_at").first()
    if contract and contract.approver:
        return True
    return False


@register.simple_tag
def contract_uploaded_by_contracting(project):
    contract = project.contracts.order_by("-created_at").first()
    if contract:
        return True
    return False


@register.simple_tag
def contract_reuploaded_by_applicant(project):
    contract = project.contracts.order_by("-created_at").first()
    if contract and contract.signed_by_applicant:
        return True
    return False


@register.simple_tag
def user_can_submit_contract(project, user, contract):
    can_submit, _ = has_permission(
        "submit_contract_documents",
        user,
        object=project,
        raise_exception=False,
        contract=contract,
    )
    return can_submit


@register.simple_tag
def required_remaining_contracting_doc_categories(remaining_categories):
    return [category for category in remaining_categories if category.required]


@register.simple_tag
def user_can_upload_contract(project, user):
    can_upload, _ = has_permission(
        "contract_upload", user, object=project, raise_exception=False
    )
    return can_upload


@register.simple_tag
def user_can_initiate_contract(user):
    if user.is_contracting:
        return True
    if user.is_apply_staff and settings.STAFF_UPLOAD_CONTRACT:
        return True
    return False


@register.simple_tag
def show_contract_upload_row(project, user):
    if project.status != CONTRACTING:
        return False
    if user.is_contracting or user == project.user or user.is_apply_staff:
        return True
    return False


@register.simple_tag
def can_update_contracting_documents(project, user):
    if project.status != CONTRACTING:
        return False
    if user == project.user and not user.is_apply_staff and not user.is_contracting:
        return True
    return False


@register.simple_tag
def can_access_category_document(project, user, category):
    permission, _ = has_permission(
        "view_contract_documents",
        user,
        object=project,
        contract_category=category,
        raise_exception=False,
    )
    return permission
