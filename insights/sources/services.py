from abc import ABC, abstractmethod
from typing import Optional, Type

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import PermissionDenied

from insights.authentication.services.jwt_service import JWTService
from insights.projects.parsers import parse_dict_to_json
from insights.sources.base import BaseQueryExecutor
from insights.sources.factories import SourceQueryExecutorFactory
from insights.sources.vtexcredentials.exceptions import VtexCredentialsNotFound
from insights.widgets.models import Widget
from insights.widgets.usecases.get_source_data import (
    cross_source_data_operation,
    simple_source_data_operation,
)


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
        source_query_executor_factory: Type[
            SourceQueryExecutorFactory
        ] = SourceQueryExecutorFactory,
    ):
        self.source_query_executor_factory = source_query_executor_factory

    def get_source_query_executor(self, source_name: str) -> Type[BaseQueryExecutor]:
        return self.source_query_executor_factory.get_source_query_executor(source_name)

    def _handle_serialized_auth(self, widget: Widget) -> dict:
        """
        Handle the serialized authentication for the widget
        """
        if widget.type != "vtex_order":
            return {}

        if widget.project.vtex_account:
            return {
                "domain": widget.project.vtex_account,
                "internal_token": JWTService().generate_jwt_token(
                    vtex_account=widget.project.vtex_account
                ),
            }

        auth_source = self.get_source_query_executor("vtexcredentials")
        try:
            return auth_source.execute(
                filters={"project": widget.project.uuid},
                operation="get_vtex_auth",
                parser=parse_dict_to_json,
                return_format="",
                query_kwargs={},
            )
        except VtexCredentialsNotFound:
            raise PermissionDenied(
                detail="VTEX credentials not configured for this project. Please configure the VTEX integration first."
            )

    def _get_extra_query_kwargs(self, widget: Widget, is_report: bool) -> dict:
        """
        Handle extra query keyword arguments based on the widget configuration
        """
        extra_query_kwargs = {}

        if (
            widget.name == "human_service_dashboard.peaks_in_human_service"
            and is_report is False
        ):
            extra_query_kwargs["timeseries_hour_kwargs"] = {
                "start_hour": 7,
                "end_hour": 18,
            }

        return extra_query_kwargs

    def get_source_data_from_widget(
        self,
        widget: Widget,
        is_report: bool = False,
        is_live: bool = False,
        filters: Optional[dict] = None,
        user_email: str = "",
    ):
        filters = filters or {}
        try:
            source = widget.source
            if is_report:
                widget = widget.report

            source_query_executor = self.get_source_query_executor(source)
            if source_query_executor is None:
                raise Exception(
                    f"could not find a source with the slug {source}, make sure that the widget is configured with a supported source"
                )

            serialized_auth = self._handle_serialized_auth(widget)

            operation_function = (
                cross_source_data_operation
                if widget.is_crossing_data
                else simple_source_data_operation
            )

            extra_query_kwargs = self._get_extra_query_kwargs(widget, is_report)

            return operation_function(
                widget=widget,
                source_query=source_query_executor,
                is_live=is_live,
                filters=filters,
                user_email=user_email,
                auth_params=serialized_auth,
                extra_query_kwargs=extra_query_kwargs,
            )

        except ObjectDoesNotExist:
            raise Exception("Widget not found.")

        except KeyError:
            raise Exception(
                "The subwidgets operation needs to be one that returns only one object value."
            )
