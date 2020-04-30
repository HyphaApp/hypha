from django.urls import include, path

from .views import (
    ContractPrivateMediaView,
    CreatePaymentRequestView,
    DeletePaymentRequestView,
    EditPaymentRequestView,
    PaymentRequestListView,
    PaymentRequestPrivateMedia,
    PaymentRequestView,
    ProjectDetailPDFView,
    ProjectDetailSimplifiedView,
    ProjectDetailUnauthenticatedView,
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
        path('unauthenticated/', ProjectDetailUnauthenticatedView.as_view(), name='unauthenticated'),
        path('request/', CreatePaymentRequestView.as_view(), name='request'),
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
]
