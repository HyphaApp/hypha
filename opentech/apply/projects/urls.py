from django.conf import settings
from django.urls import include, path

from .views import (
    DeletePaymentRequestView,
    EditPaymentRequestView,
    PaymentRequestListView,
    PaymentRequestPrivateMedia,
    PaymentRequestView,
    ProjectDetailSimplifiedView,
    ProjectDetailView,
    ProjectEditView,
    ProjectListView,
    ProjectOverviewView,
    ProjectPrivateMediaView,
)

app_name = 'projects'

urlpatterns = []

if settings.PROJECTS_ENABLED:
    urlpatterns = [
        path('', ProjectOverviewView.as_view(), name='overview'),
        path('all/', ProjectListView.as_view(), name='all'),
        path('<int:pk>/', include([
            path('', ProjectDetailView.as_view(), name='detail'),
            path('edit/', ProjectEditView.as_view(), name="edit"),
            path('documents/<int:file_pk>/', ProjectPrivateMediaView.as_view(), name="document"),
            path('simplified/', ProjectDetailSimplifiedView.as_view(), name='simplified'),
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
    ]
