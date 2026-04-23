from abc import ABC, abstractmethod
from typing import Type

from insights.sources.base import BaseQueryExecutor
from insights.sources.factories import SourceQueryExecutorFactory
from insights.widgets.models import Widget


class BaseDataSourceService(ABC):
    """
    Base class for data source services
    """

    @abstractmethod
    def get_source_query_executor(self, source_name: str):
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def get_source_data_from_widget(
        self,
        widget: Widget,
        is_report: bool = False,
        is_live: bool = False,
        filters: dict = {},
        user_email: str = "",
    ):
        raise NotImplementedError("Subclasses must implement this method")


class DataSourceService(BaseDataSourceService):
    """
    Data source service
    """

    def __init__(
        self,
        source_query_executor_factory: SourceQueryExecutorFactory = SourceQueryExecutorFactory(),
    ):
        self.source_query_executor_factory = source_query_executor_factory

    def get_source_query_executor(self, source_name: str) -> Type[BaseQueryExecutor]:
        return self.source_query_executor_factory.get_source_query_executor(source_name)

    def get_source_data_from_widget(
        self,
        widget: Widget,
        is_report: bool = False,
        is_live: bool = False,
        filters: dict = {},
        user_email: str = "",
    ):
        source_query_executor = self.get_source_query_executor(widget.source.slug)
        # TODO: Implement the logic to get the source data from the widget
