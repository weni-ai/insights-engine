from celery import shared_task
from insights.feature_flags.integrations.growthbook.instance import GROWTHBOOK_CLIENT


@shared_task
def update_growthbook_feature_flags() -> None:
    """
    Update GrowthBook feature flags definitions (curto e longo cache).
    """
    GROWTHBOOK_CLIENT.update_feature_flags_definitions()