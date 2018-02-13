from django.conf.urls import url

from .views import DashboardView, SubmissionDetailView


urlpatterns = [
    url(r'^$', DashboardView.as_view(), name="dashboard"),
    url(r'^submission/(?P<pk>\d+)/$', SubmissionDetailView.as_view(), name="submission"),
]
