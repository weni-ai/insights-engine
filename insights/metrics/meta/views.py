from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiParameter
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from django.utils import translation

from insights.authentication.permissions import ProjectAuthQueryParamPermission
from insights.metrics.meta.choices import (
    WhatsAppMessageTemplatesCategories,
    WhatsAppMessageTemplatesLanguages,
)
from insights.metrics.meta.permissions import ProjectWABAPermission
from insights.metrics.meta.schema import (
    WHATSAPP_MESSAGE_TEMPLATES_GENERAL_PARAMS,
    WHATSAPP_MESSAGE_TEMPLATES_LIST_TEMPLATES_PARAMS,
    WHATSAPP_MESSAGE_TEMPLATES_MSGS_ANALYTICS_PARAMS,
)
from insights.metrics.meta.serializers import (
    MessageTemplatesCategoriesSerializer,
    MessageTemplatesLanguagesSerializer,
    MessageTemplatesQueryParamsSerializer,
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

    @extend_schema(responses={status.HTTP_200_OK: MessageTemplatesCategoriesSerializer})
    @action(
        detail=False,
        methods=["get"],
        url_name="categories",
        url_path="categories",
        permission_classes=[IsAuthenticated],
    )
    def categories(self, request: Request) -> Response:
        all_categories = [
            {
                "value": category.value,
                "display_name": category.label,
            }
            for category in WhatsAppMessageTemplatesCategories
        ]

        return Response({"categories": all_categories}, status=status.HTTP_200_OK)

    @extend_schema(responses={status.HTTP_200_OK: MessageTemplatesLanguagesSerializer})
    @action(
        detail=False,
        methods=["get"],
        url_name="languages",
        url_path="languages",
        permission_classes=[IsAuthenticated],
    )
    def languages(self, request: Request) -> Response:
        with translation.override(request.headers.get("Accept-Language", "en")):
            all_languages = [
                {
                    "value": language.value,
                    "display_name": language.label,
                }
                for language in WhatsAppMessageTemplatesLanguages
            ]

        return Response({"languages": all_languages}, status=status.HTTP_200_OK)
