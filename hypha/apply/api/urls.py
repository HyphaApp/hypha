from django.urls import include, path

from .v1 import urls as v1_urls

app_name = "api"

schema_url_patterns_v1 = [
    path("api/v1/", include(v1_urls)),
]

urlpatterns = [
    path("v1/", include(v1_urls)),
]
