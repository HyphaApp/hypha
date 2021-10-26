from django.urls import include, path

from .views import (
    ContractPrivateMediaView,
    CreateInvoiceView,
    CreatePaymentRequestView,
    CreateVendorView,
    DeleteInvoiceView,
    DeletePaymentRequestView,
    EditInvoiceView,
    EditPaymentRequestView,
    InvoiceListView,
    InvoicePrivateMedia,
    InvoiceView,
    PaymentRequestListView,
    PaymentRequestPrivateMedia,
    PaymentRequestView,
    ProjectDetailPDFView,
    ProjectDetailSimplifiedView,
    ProjectDetailView,
    ProjectEditView,
    ProjectListView,
    ProjectOverviewView,
    ProjectPrivateMediaView,
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
    path('<int:pk>/', include([
        path('', ProjectDetailView.as_view(), name='detail'),
        path('edit/', ProjectEditView.as_view(), name="edit"),
        path('documents/<int:file_pk>/', ProjectPrivateMediaView.as_view(), name="document"),
        path('contract/<int:file_pk>/', ContractPrivateMediaView.as_view(), name="contract"),
        path('download/', ProjectDetailPDFView.as_view(), name='download'),
        path('simplified/', ProjectDetailSimplifiedView.as_view(), name='simplified'),
        path('request/', CreatePaymentRequestView.as_view(), name='request'),
        path('invoice/', CreateInvoiceView.as_view(), name='invoice'),
        path('vendor/', CreateVendorView.as_view(), name='vendor'),
        path('vendor/<int:vendor_pk>/', VendorDetailView.as_view(), name='vendor-detail'),
        path('vendor/<int:vendor_pk>/documents/<int:file_pk>/', VendorPrivateMediaView.as_view(), name='vendor-documents'),
        path('invoices/', InvoiceListView.as_view(), name='invoices'),
        path('invoices/<int:invoice_pk>/', include([
            path('', InvoiceView.as_view(), name='invoice-detail'),
            path('edit/', EditInvoiceView.as_view(), name='invoice-edit'),
            path('delete/', DeleteInvoiceView.as_view(), name='invoice-delete'),
            path('documents/invoice/', InvoicePrivateMedia.as_view(), name="invoice-document"),
            path('documents/supporting/<int:file_pk>/', InvoicePrivateMedia.as_view(), name="invoice-supporting-document"),
        ])),
    ])),
    path('payment-requests/', include(([
        path('', PaymentRequestListView.as_view(), name='all'),
        path('<int:pk>/', include([
            path('', PaymentRequestView.as_view(), name='detail'),
            path('edit/', EditPaymentRequestView.as_view(), name='edit'),
            path('delete/', DeletePaymentRequestView.as_view(), name='delete'),
            path('documents/invoice/', PaymentRequestPrivateMedia.as_view(), name="invoice"),
            path('documents/receipt/<int:file_pk>/', PaymentRequestPrivateMedia.as_view(), name="receipt"),
        ])),
    ], 'payments'))),
    path('reports/', include(([
        path('', ReportListView.as_view(), name='all'),
        path('<int:pk>/', include([
            path('', ReportDetailView.as_view(), name='detail'),
            path('skip/', ReportSkipView.as_view(), name='skip'),
            path('edit/', ReportUpdateView.as_view(), name='edit'),
            path('documents/<int:file_pk>/', ReportPrivateMedia.as_view(), name="document"),
        ])),
    ], 'reports'))),
    path('venor/', include(([
        path('', ReportListView.as_view(), name='all'),
        path('<int:pk>/', include([
            path('', ReportDetailView.as_view(), name='detail'),
            path('skip/', ReportSkipView.as_view(), name='skip'),
            path('edit/', ReportUpdateView.as_view(), name='edit'),
            path('documents/<int:file_pk>/', ReportPrivateMedia.as_view(), name="document"),
        ])),
    ], 'reports'))),
]
