from django.urls import path

from .views import ProjectDetailView

urlpatterns = [
    path('<int:pk>/', ProjectDetailView.as_view(), name='detail'),
]
