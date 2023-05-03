from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET
from django import forms

from hypha.apply.activity.services import (
    get_related_actions_for_user,
)

from ..models.project import Project, DocumentCategory
from ..forms.project import UploadDocumentForm


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
    project = get_object_or_404(Project, pk=pk)
    document_category = get_object_or_404(DocumentCategory, pk=category_pk)
    form = UploadDocumentForm(request.user)
    form_category = form.fields['category']
    form_category.initial = document_category
    form_category.widget = forms.HiddenInput()
    ctx = {
        'header': "Upload supporting documents",
        'document_form': form,
    }
    return render(request, 'application_projects/partials/upload_document_modal.html', ctx)
