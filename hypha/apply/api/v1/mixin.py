from django.shortcuts import get_object_or_404

from hypha.apply.funds.models import ApplicationSubmission
from hypha.apply.projects.models import Invoice, Project


class SubmissionNestedMixin:
    def get_submission_object(self):
        return get_object_or_404(
            ApplicationSubmission, id=self.kwargs['submission_pk']
        )


class InvoiceNestedMixin:
    def get_invoice_object(self):
        return get_object_or_404(
            Invoice, id=self.kwargs['invoice_pk']
        )


class ProjectNestedMixin:
    def get_project_object(self):
        return get_object_or_404(
            Project, id=self.kwargs['project_pk']
        )
