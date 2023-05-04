from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from hypha.apply.activity.services import (
    get_related_actions_for_user,
)
from hypha.apply.utils.views import DelegateableView

from ..models.project import DocumentCategory, Project


@login_required
@require_GET
def partial_project_activities(request, pk):
    project = get_object_or_404(Project, pk=pk)
    ctx = {
        'actions': get_related_actions_for_user(project, request.user)
    }
    return render(request, 'activity/include/action_list.html', ctx)


@login_required
@require_GET
def partial_document_category_form(request, pk, category_pk):
    from hypha.apply.projects.views.project import UploadDocumentView
    get_object_or_404(Project, pk=pk)
    document_category = get_object_or_404(DocumentCategory, pk=category_pk)
    form = UploadDocumentView.form_class(request.user)
    form_category = form.fields['category']
    form_category.initial = document_category
    form_category.widget = forms.HiddenInput()
    form_prefix = DelegateableView.form_prefix
    form_view_name = UploadDocumentView.context_name
    form.name = f'{form_prefix}{form_view_name}'
    ctx = {
        'header': "Upload supporting documents",
        'document_form': form,
        'form_id': f'{form_view_name}-{category_pk}'
    }
    return render(request, 'application_projects/partials/upload_document_modal.html', ctx)
