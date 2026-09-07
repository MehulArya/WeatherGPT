from django.contrib import admin

from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("title", "alert_type", "severity", "location_name", "starts_at", "is_official")
    list_filter = ("alert_type", "severity", "is_official")
    search_fields = ("title", "location_name")