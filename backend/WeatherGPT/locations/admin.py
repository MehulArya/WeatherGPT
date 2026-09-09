from django.contrib import admin

from locations.models import SavedLocation


@admin.register(SavedLocation)
class SavedLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "client_key", "created_at")
    list_filter = ("country",)
    search_fields = ("name", "client_key")
