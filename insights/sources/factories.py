from abc import ABC, abstractmethod
from typing import Type
from django.utils.module_loading import import_string

import logging

from insights.sources.base import BaseQueryExecutor

logger = logging.getLogger(__name__)


class BaseSourceQueryExecutorFactory(ABC):
    """
    Base class for source query executor factories
    """

    @abstractmethod
    @classmethod
    def get_source_query_executor(cls, source_name: str) -> Type[BaseQueryExecutor]:
        raise NotImplementedError("Subclasses must implement this method")


class SourceQueryExecutorFactory(BaseSourceQueryExecutorFactory):
    """
    Factory for source query executors
    """

    @classmethod
    def get_source_query_executor(cls, source_name: str) -> Type[BaseQueryExecutor]:
        try:
            source_path = (
                f"insights.sources.{source_name}.usecases.query_execute.QueryExecutor"
            )
            return import_string(source_path)
        except (ModuleNotFoundError, ImportError, AttributeError) as e:
            logger.warning(f"Source '{source_name}' not available: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading source '{source_name}': {e}")
            return None
