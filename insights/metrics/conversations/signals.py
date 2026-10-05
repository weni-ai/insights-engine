from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from insights.dashboards.models import CONVERSATIONS_DASHBOARD_NAME
from insights.metrics.conversations.usecases.should_show_dashboard_mock import (
    ShouldShowConversationsDashboardMockUseCase,
)
from insights.widgets.models import Widget


def _get_conversations_dashboard_project_uuid(widget: Widget):
    dashboard = widget.dashboard
    if dashboard is None and widget.parent_id:
        dashboard = getattr(widget.parent, "dashboard", None)

    if dashboard is None or dashboard.name != CONVERSATIONS_DASHBOARD_NAME:
        return None

    return dashboard.project_id


@receiver(post_save, sender=Widget)
@receiver(post_delete, sender=Widget)
def invalidate_should_show_mock_cache(sender, instance, **kwargs):
    project_uuid = _get_conversations_dashboard_project_uuid(instance)
    if project_uuid is None:
        return

    ShouldShowConversationsDashboardMockUseCase.invalidate(project_uuid)
