from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from .v1 import urls as v1_urls

app_name = "api"

schema_url_patterns_v1 = [
    path("api/v1/", include(v1_urls)),
]

schema_view_v1 = get_schema_view(
    openapi.Info(
        title="Hypha API",
        default_version="v1",
        description="Hypha APIs specification",
    ),
    public=False,
    patterns=schema_url_patterns_v1,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("v1/", include(v1_urls)),
    path(
        "v1/doc/",
        schema_view_v1.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
]
