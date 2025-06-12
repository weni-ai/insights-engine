import logging

from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


def get_source(slug: str):
    try:
        source_path = f"insights.sources.{slug}.usecases.query_execute.QueryExecutor"
        return import_string(source_path)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        logger.warning(f"Source '{slug}' not available: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading source '{slug}': {e}")
        return None
