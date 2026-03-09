from django.contrib import admin
from .models import APIKey

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ("service_name", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("service_name", "description")
