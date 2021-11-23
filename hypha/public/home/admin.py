from django.contrib import admin
from rest_framework_api_key.admin import APIKeyModelAdmin
from .models import PublicAPIKey


@admin.register(PublicAPIKey)
class PublicAPIKeyModelAdmin(APIKeyModelAdmin):
    pass
