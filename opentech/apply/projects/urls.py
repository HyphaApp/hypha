from django.conf import settings
from django.urls import include, path

from .views import ProjectDetailView, ProjectEditView, ProjectPrivateMediaView

app_name = 'projects'

urlpatterns = []

if settings.PROJECTS_ENABLED:
    urlpatterns = [
        path('<int:pk>/', include([
            path('', ProjectDetailView.as_view(), name='detail'),
            path('edit/', ProjectEditView.as_view(), name="edit"),
            path('documents/<int:file_pk>/', ProjectPrivateMediaView.as_view(), name="document"),
        ])),
    ]
