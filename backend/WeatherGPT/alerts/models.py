from django.db import models


class Alert(models.Model):
    """A prototype weather alert produced by the rule engine (never official)."""

    class AlertType(models.TextChoices):
        RAIN = "rain", "Rain"
        HEAT = "heat", "Heat"
        WIND = "wind", "Wind"

    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    location_name = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=8, decimal_places=5)
    longitude = models.DecimalField(max_digits=9, decimal_places=5)
    alert_type = models.CharField(max_length=16, choices=AlertType.choices)
    severity = models.CharField(max_length=16, choices=Severity.choices)
    title = models.CharField(max_length=200)
    description = models.TextField()
    advice = models.TextField(blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    source = models.CharField(max_length=100, default="prototype-rule-engine")
    is_official = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-starts_at"]
        indexes = [
            models.Index(fields=["latitude", "longitude", "starts_at"]),
        ]

    def __str__(self):
        return f"{self.get_alert_type_display()} ({self.get_severity_display()}) @ {self.location_name}"