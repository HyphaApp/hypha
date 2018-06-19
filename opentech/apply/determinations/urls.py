from django.urls import path

from .views import DeterminationCreateOrUpdateView, DeterminationDetailView

app_name = 'determinations'

urlpatterns = [
    path('determination/', DeterminationDetailView.as_view(), name="detail"),
    path('determination/create', DeterminationCreateOrUpdateView.as_view(), name="form"),
]
