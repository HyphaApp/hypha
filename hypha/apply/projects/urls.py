from django.urls import include, path

from .views import (
    ContractDocumentPrivateMediaView,
    ContractPrivateMediaView,
    CreateInvoiceView,
    CreateVendorView,
    DeleteInvoiceView,
    EditInvoiceView,
    InvoiceListView,
    InvoicePrivateMedia,
    InvoiceView,
    ProjectApprovalFormEditView,
    ProjectDetailApprovalView,
    ProjectDetailDownloadView,
    ProjectDetailView,
    ProjectListView,
    ProjectOverviewView,
    ProjectPrivateMediaView,
    ProjectSOWDownloadView,
    ProjectSOWView,
    ReportDetailView,
    ReportListView,
    ReportPrivateMedia,
    ReportSkipView,
    ReportUpdateView,
    VendorDetailView,
    VendorPrivateMediaView,
)

app_name = 'projects'

urlpatterns = [
    path('', ProjectOverviewView.as_view(), name='overview'),
    path('all/', ProjectListView.as_view(), name='all'),
    path('invoices/', InvoiceListView.as_view(), name='invoices'),

    path('<int:pk>/', include([
        path('', ProjectDetailView.as_view(), name='detail'),
        path('edit/', ProjectApprovalFormEditView.as_view(), name="edit"),
        path('documents/<int:file_pk>/', ProjectPrivateMediaView.as_view(), name="document"),
        path('contract/<int:file_pk>/', ContractPrivateMediaView.as_view(), name="contract"),
        path('contract/documents/<int:file_pk>/', ContractDocumentPrivateMediaView.as_view(), name="contract_document"),
        path('download/<str:export_type>/', ProjectDetailDownloadView.as_view(), name='download'),
        path('approval/', ProjectDetailApprovalView.as_view(), name='approval'),
        path('sow/', ProjectSOWView.as_view(), name='sow'),
        path('sow/download/<str:export_type>/', ProjectSOWDownloadView.as_view(), name='download-sow'),
        path('invoice/', CreateInvoiceView.as_view(), name='invoice'),
        path('vendor/', CreateVendorView.as_view(), name='vendor'),
        path('vendor/<int:vendor_pk>/', VendorDetailView.as_view(), name='vendor-detail'),
        path('vendor/<int:vendor_pk>/documents/<int:file_pk>/', VendorPrivateMediaView.as_view(), name='vendor-documents'),
        path('invoices/<int:invoice_pk>/', include([
            path('', InvoiceView.as_view(), name='invoice-detail'),

            path('edit/', EditInvoiceView.as_view(), name='invoice-edit'),
            path('delete/', DeleteInvoiceView.as_view(), name='invoice-delete'),
            path('documents/invoice/', InvoicePrivateMedia.as_view(), name="invoice-document"),
            path('documents/supporting/<int:file_pk>/', InvoicePrivateMedia.as_view(), name="invoice-supporting-document"),
        ])),
    ])),

    path('reports/', include(([
        path('', ReportListView.as_view(), name='all'),
        path('<int:pk>/', include([
            path('', ReportDetailView.as_view(), name='detail'),
            path('skip/', ReportSkipView.as_view(), name='skip'),
            path('edit/', ReportUpdateView.as_view(), name='edit'),
            path('documents/<int:file_pk>/', ReportPrivateMedia.as_view(), name="document"),
        ])),
    ], 'reports'))),
    path('vendor/', include(([
        path('', ReportListView.as_view(), name='all'),
        path('<int:pk>/', include([
            path('', ReportDetailView.as_view(), name='detail'),
            path('skip/', ReportSkipView.as_view(), name='skip'),
            path('edit/', ReportUpdateView.as_view(), name='edit'),
            path('documents/<int:file_pk>/', ReportPrivateMedia.as_view(), name="document"),
        ])),
    ], 'reports'))),
]
