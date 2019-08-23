from django.conf import settings
from django.urls import include, path

from .views import (
    ApproveContractView,
    ChangePaymentRequestStatusView,
    DeletePaymentRequestView,
    EditPaymentRequestView,
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
            path(
                'delete-payment-request/<int:payment_request_id>/',
                DeletePaymentRequestView.as_view(),
                name='delete-payment-request',
            ),
            path(
                'edit-payment-request/<int:payment_request_id>/',
                EditPaymentRequestView.as_view(),
                name='edit-payment-request',
            ),
            path('simplified/', ProjectDetailSimplifiedView.as_view(), name='simplified'),
        ])),
    ]
