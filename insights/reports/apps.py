from django.apps import AppConfig


class ReportsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "insights.reports"

    def ready(self):
        import insights.reports.signals  # noqa: F401
