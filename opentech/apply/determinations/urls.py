from django.urls import path

from .views import DeterminationCreateOrUpdateView, DeterminationDetailView

app_name = 'determinations'

urlpatterns = [
    path('determination/', DeterminationDetailView.as_view(), name="detail"),
    path('determination/add', DeterminationCreateOrUpdateView.as_view(), name="form"),
]
