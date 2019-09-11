from django.conf import settings
from django.urls import include, path

from .views import (
    ApproveContractView,
    ChangePaymentRequestStatusView,
    DeletePaymentRequestView,
    EditPaymentRequestView,
    PaymentRequestView,
    PaymentRequestPrivateMedia,
    ProjectDetailSimplifiedView,
    ProjectDetailView,
    ProjectEditView,
    ProjectPrivateMediaView,
    SelectDocumentView
)

app_name = 'projects'

urlpatterns = []

if settings.PROJECTS_ENABLED:
    urlpatterns = [
        path('<int:pk>/', include([
            path('', ProjectDetailView.as_view(), name='detail'),
            path('edit/', ProjectEditView.as_view(), name="edit"),
            path(
                'approve-contract/<int:contract_pk>/',
                ApproveContractView.as_view(),
                name="approve-contract",
            ),
            path('documents/<int:file_pk>/', ProjectPrivateMediaView.as_view(), name="document"),
            path(
                'change-payment-request-status/<int:payment_request_id>/',
                ChangePaymentRequestStatusView.as_view(),
                name='change-payment-status',
            ),
            path(
                'copy-documents/',
                SelectDocumentView.as_view(),
                name="copy-documents",
            ),
            path('simplified/', ProjectDetailSimplifiedView.as_view(), name='simplified'),
            path('payment-requests/<int:pr_pk>/', include(([
                path('', PaymentRequestView.as_view(), name='detail'),
                path('edit/', EditPaymentRequestView.as_view(), name='edit'),
                path('delete/', DeletePaymentRequestView.as_view(), name='delete'),
                path('documents/invoice/', PaymentRequestPrivateMedia.as_view(), name="invoice"),
                path('documents/receipt/<int:file_pk>/', PaymentRequestPrivateMedia.as_view(), name="receipt"),
            ], 'payments'))),
        ])),
    ]
