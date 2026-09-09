from django.db import models


class SavedLocation(models.Model):
    """A city bookmarked by an anonymous client (client_key kept in localStorage)."""

    client_key = models.CharField(max_length=64, db_index=True)
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=200, blank=True, default="")
    latitude = models.DecimalField(max_digits=8, decimal_places=5)
    longitude = models.DecimalField(max_digits=9, decimal_places=5)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["client_key", "created_at"])]

    def __str__(self):
        return f"{self.name} ({self.client_key})"
