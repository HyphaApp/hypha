from django.urls import path

from .views import DeterminationCreateOrUpdateView, DeterminationDetailView

app_name = 'determinations'

urlpatterns = [
    path('determination/', DeterminationCreateOrUpdateView.as_view(), name="form"),
    path('determination/<int:pk>', DeterminationDetailView.as_view(), name="determination"),
]
