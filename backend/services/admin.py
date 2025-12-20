from django.contrib import admin
from .models import Service

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
