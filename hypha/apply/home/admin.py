from django.contrib import admin
from rest_framework_api_key.admin import APIKeyModelAdmin
from .models import ApplyAPIKey


@admin.register(ApplyAPIKey)
class ApplyAPIKeyModelAdmin(APIKeyModelAdmin):
    pass
