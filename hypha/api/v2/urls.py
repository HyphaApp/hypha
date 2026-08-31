from django.urls import path

from .views import open_calls_json

app_name = "v2"

urlpatterns = [
    path("open-calls.json", open_calls_json),
]
