from django.conf.urls import url

from .views import DashboardView, SearchView


urlpatterns = [
    url(r'^$', DashboardView.as_view(), name="dashboard"),
    url(r'^search$', SearchView.as_view(), name="search"),
]
