from django.conf.urls import url

from .views import ApplicantDashboardView, DashboardView


urlpatterns = [
    url(r'^$', DashboardView.as_view(), name="dashboard"),
    url(r'^applicant/$', ApplicantDashboardView.as_view(), name="dashboard"),
]
