from django.urls import include, path
from django.views.generic import RedirectView

from .views import (
    ApproveContractView,
    BatchUpdateInvoiceStatusView,
    CategoryTemplatePrivateMediaView,
    ChangeInvoiceStatusView,
    ChangePAFStatusView,
    ChangeProjectstatusView,
    ContractDocumentPrivateMediaView,
    ContractPrivateMediaView,
    CreateInvoiceView,
    DeleteInvoiceView,
    EditInvoiceView,
    InvoiceListView,
    InvoicePrivateMedia,
    InvoiceView,
    ProjectDetailApprovalView,
    ProjectDetailDownloadView,
    ProjectDetailView,
    ProjectFormEditView,
    ProjectListView,
    ProjectPrivateMediaView,
    ProjectSOWDownloadView,
    ProjectSOWView,
    RemoveContractDocumentView,
    RemoveDocumentView,
    ReportDetailView,
    ReportFrequencyUpdate,
    ReportingView,
    ReportListView,
    ReportPrivateMedia,
    ReportSkipView,
    ReportUpdateView,
    SendForApprovalView,
    SkipPAFApprovalProcessView,
    SubmitContractDocumentsView,
    UpdateAssignApproversView,
    UpdateLeadView,
    UpdatePAFApproversView,
    UpdateProjectTitleView,
    UploadContractDocumentView,
    UploadContractView,
    UploadDocumentView,
    get_invoices_status_counts,
    get_project_status_counts,
    partial_contracting_documents,
    partial_get_invoice_detail_actions,
    partial_get_invoice_status,
    partial_get_invoice_status_table,
    partial_project_activities,
    partial_project_lead,
    partial_project_title,
    partial_supporting_documents,
)

app_name = "projects"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="apply:projects:all"), name="overview"),
    path("all/", ProjectListView.as_view(), name="all"),
    path("statuses/", get_project_status_counts, name="projects_status_counts"),
    path("invoices/", InvoiceListView.as_view(), name="invoices"),
    path(
        "invoices/statuses/", get_invoices_status_counts, name="invoices_status_counts"
    ),
    path(
        "all/bulk_invoice_status_update/",
        BatchUpdateInvoiceStatusView.as_view(),
        name="bulk_invoice_status_update",
    ),
    path(
        "<int:pk>/",
        include(
            [
                path("", ProjectDetailView.as_view(), name="detail"),
                path(
                    "partial/activities/",
                    partial_project_activities,
                    name="partial-activities",
                ),
                path("partial/lead/", partial_project_lead, name="project_lead"),
                path("partial/title/", partial_project_title, name="project_title"),
                path("edit/", ProjectFormEditView.as_view(), name="edit"),
                path("lead/update/", UpdateLeadView.as_view(), name="lead_update"),
                path(
                    "status/update/",
                    ChangeProjectstatusView.as_view(),
                    name="project_status_update",
                ),
                path(
                    "title/update/",
                    UpdateProjectTitleView.as_view(),
                    name="project_title_update",
                ),
                path(
                    "paf/skip/", SkipPAFApprovalProcessView.as_view(), name="paf_skip"
                ),
                path(
                    "documents/submit/",
                    SendForApprovalView.as_view(),
                    name="submit_project_for_approval",
                ),
                path(
                    "pafapprovers/assign/",
                    UpdateAssignApproversView.as_view(),
                    name="assign_pafapprovers",
                ),
                path(
                    "pafapprovers/update/",
                    UpdatePAFApproversView.as_view(),
                    name="update_pafapprovers",
                ),
                path(
                    "pafstatus/update/",
                    ChangePAFStatusView.as_view(),
                    name="update_pafstatus",
                ),
                path(
                    "document/<int:category_pk>/upload/",
                    UploadDocumentView.as_view(),
                    name="supporting_doc_upload",
                ),
                path(
                    "document/<int:document_pk>/remove/",
                    RemoveDocumentView.as_view(),
                    name="remove_supporting_document",
                ),
                path(
                    "partial/documents/",
                    partial_supporting_documents,
                    name="supporting_documents",
                ),
                path(
                    "documents/<int:file_pk>",
                    ProjectPrivateMediaView.as_view(),
                    name="document",
                ),
                path(
                    "documents/<uuid:field_id>/<str:file_name>",
                    ProjectPrivateMediaView.as_view(),
                    name="document",
                ),
                path(
                    "contract/upload/",
                    UploadContractView.as_view(),
                    name="contract_upload",
                ),
                path(
                    "partial/contract/documents/",
                    partial_contracting_documents,
                    name="contract_documents",
                ),
                path(
                    "contract/documents/<int:category_pk>/upload/",
                    UploadContractDocumentView.as_view(),
                    name="contract_doc_upload",
                ),
                path(
                    "contract/documents/<int:document_pk>/remove/",
                    RemoveContractDocumentView.as_view(),
                    name="remove_contracting_document",
                ),
                path(
                    "category/<str:type>/<int:category_pk>/template/",
                    CategoryTemplatePrivateMediaView.as_view(),
                    name="category_template",
                ),
                path(
                    "contract/<int:file_pk>/",
                    ContractPrivateMediaView.as_view(),
                    name="contract",
                ),
                path(
                    "contract/documents/<int:file_pk>/",
                    ContractDocumentPrivateMediaView.as_view(),
                    name="contract_document",
                ),
                path(
                    "contract/documents/submit/",
                    SubmitContractDocumentsView.as_view(),
                    name="contract_documents_submit",
                ),
                path(
                    "contract/approve/",
                    ApproveContractView.as_view(),
                    name="contract_approve",
                ),
                path(
                    "download/<str:export_type>/",
                    ProjectDetailDownloadView.as_view(),
                    name="download",
                ),
                path("approval/", ProjectDetailApprovalView.as_view(), name="approval"),
                path("sow/", ProjectSOWView.as_view(), name="sow"),
                path(
                    "sow/download/<str:export_type>/",
                    ProjectSOWDownloadView.as_view(),
                    name="download-sow",
                ),
                path(
                    "frequency/update/",
                    ReportFrequencyUpdate.as_view(),
                    name="report_frequency_update",
                ),
                path("invoice/", CreateInvoiceView.as_view(), name="invoice"),
                path(
                    "partial/invoice-status/",
                    partial_get_invoice_status_table,
                    name="partial-invoices-status",
                ),
                path(
                    "partial/rejected-invoice-status/",
                    partial_get_invoice_status_table,
                    {"rejected": True},
                    name="partial-rejected-invoices-status",
                ),
                path(
                    "invoices/<int:invoice_pk>/",
                    include(
                        [
                            path("", InvoiceView.as_view(), name="invoice-detail"),
                            path(
                                "edit/", EditInvoiceView.as_view(), name="invoice-edit"
                            ),
                            path(
                                "update/",
                                ChangeInvoiceStatusView.as_view(),
                                name="invoice-update",
                            ),
                            path(
                                "delete/",
                                DeleteInvoiceView.as_view(),
                                name="invoice-delete",
                            ),
                            path(
                                "partial/status/",
                                partial_get_invoice_status,
                                name="partial-invoice-status",
                            ),
                            path(
                                "actions/",
                                partial_get_invoice_detail_actions,
                                name="partial-invoice-detail-actions",
                            ),
                            path(
                                "documents/invoice/",
                                InvoicePrivateMedia.as_view(),
                                name="invoice-document",
                            ),
                            path(
                                "documents/supporting/<int:file_pk>/",
                                InvoicePrivateMedia.as_view(),
                                name="invoice-supporting-document",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    path(
        "reports/",
        include(
            (
                [
                    path("", ReportListView.as_view(), name="submitted"),
                    path("all/", ReportingView.as_view(), name="all"),
                    path(
                        "<int:pk>/",
                        include(
                            [
                                path("", ReportDetailView.as_view(), name="detail"),
                                path("skip/", ReportSkipView.as_view(), name="skip"),
                                path("edit/", ReportUpdateView.as_view(), name="edit"),
                                path(
                                    "documents/<int:file_pk>/",
                                    ReportPrivateMedia.as_view(),
                                    name="document",
                                ),
                            ]
                        ),
                    ),
                ],
                "reports",
            )
        ),
    ),
]
