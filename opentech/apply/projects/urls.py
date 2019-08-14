from django.conf import settings
from django.urls import include, path

from .views import ProjectDetailView, ProjectEditView

app_name = 'projects'

urlpatterns = []

if settings.PROJECTS_ENABLED:
    urlpatterns = [
        path('<int:pk>/', include([
            path('', ProjectDetailView.as_view(), name='detail'),
            path('edit/', ProjectEditView.as_view(), name="edit"),
        ])),
    ]
