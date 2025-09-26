from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "insights.core"

    def ready(self):
        from insights.core.shutdown import setup_signal_handlers

        setup_signal_handlers()
