from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated

from insights.authentication.permissions import ProjectAuthQueryParamPermission
from insights.dashboards.models import Dashboard
from insights.metrics.meta.permissions import ProjectWABAPermission
from insights.metrics.meta.schema import (
    WHATSAPP_MESSAGE_TEMPLATES_GENERAL_PARAMS,
    WHATSAPP_MESSAGE_TEMPLATES_LIST_TEMPLATES_PARAMS,
    WHATSAPP_MESSAGE_TEMPLATES_MSGS_ANALYTICS_PARAMS,
)
from insights.metrics.meta.serializers import (
    FavoriteTemplateListSerializer,
    FavoriteTemplatesQueryParamsSerializer,
    MessageTemplatesQueryParamsSerializer,
    AddTemplateToFavoritesSerializer,
    RemoveTemplateFromFavoritesSerializer,
)
from insights.sources.meta_message_templates.enums import Operations
from insights.sources.meta_message_templates.usecases.query_execute import QueryExecutor


class WhatsAppMessageTemplatesView(GenericViewSet):
    query_executor = QueryExecutor
    permission_classes = [ProjectAuthQueryParamPermission, ProjectWABAPermission]

    @extend_schema(parameters=WHATSAPP_MESSAGE_TEMPLATES_LIST_TEMPLATES_PARAMS)
    @action(
        detail=False,
        methods=["get"],
        url_name="list-templates",
        url_path="list-templates",
    )
    def list_templates(self, request: Request) -> Response:
        serializer = MessageTemplatesQueryParamsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = self.query_executor.execute(
            filters=serializer.validated_data, operation=Operations.LIST_TEMPLATES.value
        )

        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(parameters=WHATSAPP_MESSAGE_TEMPLATES_GENERAL_PARAMS)
    @action(detail=False, methods=["get"], url_name="preview", url_path="preview")
    def preview_template(self, request: Request) -> Response:
        data = self.query_executor.execute(
            filters=request.query_params, operation=Operations.TEMPLATE_PREVIEW.value
        )

        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(parameters=WHATSAPP_MESSAGE_TEMPLATES_MSGS_ANALYTICS_PARAMS)
    @action(
        detail=False,
        methods=["get"],
        url_name="messages-analytics",
        url_path="messages-analytics",
    )
    def messages_analytics(self, request: Request) -> Response:
        data = self.query_executor.execute(
            filters=request.query_params, operation=Operations.MESSAGES_ANALYTICS.value
        )

        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(parameters=WHATSAPP_MESSAGE_TEMPLATES_MSGS_ANALYTICS_PARAMS)
    @action(
        detail=False,
        methods=["get"],
        url_name="buttons-analytics",
        url_path="buttons-analytics",
    )
    def buttons_analytics(self, request: Request) -> Response:
        data = self.query_executor.execute(
            filters=request.query_params, operation=Operations.BUTTONS_ANALYTICS.value
        )

        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        request=AddTemplateToFavoritesSerializer,
        responses={204: "No Content"},
    )
    @action(
        detail=False,
        methods=["post"],
        url_name="add-template-to-favorites",
        url_path="add-template-to-favorites",
        permission_classes=[IsAuthenticated],
    )
    def add_template_to_favorites(self, request: Request) -> Response:
        serializer = AddTemplateToFavoritesSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        request=RemoveTemplateFromFavoritesSerializer,
        responses={204: "No Content"},
    )
    @action(
        detail=False,
        methods=["post"],
        url_name="remove-template-from-favorites",
        url_path="remove-template-from-favorites",
        permission_classes=[IsAuthenticated],
    )
    def remove_template_from_favorites(self, request: Request) -> Response:
        serializer = RemoveTemplateFromFavoritesSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    # TODO: Add schema
    @action(
        detail=False,
        methods=["get"],
        url_name="favorites",
        url_path="favorites",
        permission_classes=[IsAuthenticated],
    )
    def favorite_templates(self, request: Request) -> Response:
        serializer = FavoriteTemplatesQueryParamsSerializer(
            data=request.query_params, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
