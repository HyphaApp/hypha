from django.urls import include, path

from .v2 import urls as v2_urls

app_name = "api"

urlpatterns = [
    path("v2/", include(v2_urls)),
]
