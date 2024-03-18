from django.urls import path

from .views import DashboardView
from .views_partials import applicant_projects, applicant_submissions

app_name = "dashboard"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("applicant/submissions/", applicant_submissions, name="applicant_submissions"),
    path("applicant/projects/", applicant_projects, name="applicant_projects"),
]
