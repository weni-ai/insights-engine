from django.db import models


class FavoriteTemplate(models.Model):
    dashboard = models.ForeignKey(
        "dashboards.Dashboard",
        on_delete=models.CASCADE,
        related_name="favorite_templates",
    )
    template_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ("dashboard", "template_id")

    def __str__(self):
        return f"{self.dashboard.name} - {self.template_id}"
