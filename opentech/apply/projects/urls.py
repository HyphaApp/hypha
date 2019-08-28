from django.conf import settings
from django.urls import include, path

from .views import (
    ApproveContractView,
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
                'copy-documents/',
                SelectDocumentView.as_view(),
                name="copy-documents",
            ),
            path('simplified/', ProjectDetailSimplifiedView.as_view(), name='simplified'),
        ])),
    ]
