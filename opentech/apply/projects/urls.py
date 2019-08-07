from django.urls import include, path

from .views import ProjectDetailView, ProjectEditView

urlpatterns = [
    path('<int:pk>/', include([
        path('', ProjectDetailView.as_view(), name='detail'),
        path('edit/', ProjectEditView.as_view(), name="edit"),
    ])),
]
