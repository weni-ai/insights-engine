from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from insights.authentication.permissions import (
    InternalAuthenticationPermission,
    ProjectAuthQueryParamPermission,
)
from insights.dashboards.models import Dashboard
from insights.metrics.meta.models import FavoriteTemplate
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
    WhatsappIntegrationWebhookRemoveSerializer,
    FavoriteTemplatesQueryParamsSerializer,
    FavoriteTemplatesSerializer,
    MessageTemplatesQueryParamsSerializer,
    AddTemplateToFavoritesSerializer,
    RemoveTemplateFromFavoritesSerializer,
    MessageTemplatesCategoriesSerializer,
    MessageTemplatesLanguagesSerializer,
    WhatsappIntegrationWebhookSerializer,
)
from insights.projects.models import Project
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
        responses={200: FavoriteTemplatesSerializer},
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

        preview_filters = {
            "template_id": serializer.validated_data["template_id"],
        }

        template_preview = self.query_executor.execute(
            filters=preview_filters, operation=Operations.TEMPLATE_PREVIEW.value
        )
        template_name = template_preview.get("name")

        serializer.context["template_name"] = template_name
        favorite = serializer.save()

        return Response(
            FavoriteTemplatesSerializer(favorite).data,
            status=status.HTTP_200_OK,
        )

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

    @extend_schema(
        parameters=FavoriteTemplatesQueryParamsSerializer,
        responses={status.HTTP_200_OK: FavoriteTemplatesSerializer(many=True)},
    )
    @action(
        detail=False,
        methods=["get"],
        url_name="favorites",
        url_path="favorites",
        permission_classes=[IsAuthenticated],
    )
    def get_favorite_templates(self, request: Request) -> Response:
        serializer = FavoriteTemplatesQueryParamsSerializer(
            data=request.query_params, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        favorites_queryset = FavoriteTemplate.objects.filter(
            dashboard=serializer.validated_data["dashboard"]
        )

        page = self.paginate_queryset(favorites_queryset)

        if page is not None:
            serializer = FavoriteTemplatesSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = FavoriteTemplatesSerializer(favorites_queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
                "name": category.label,
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
        all_languages = [
            {
                "value": language.value,
                "name": language.label,
            }
            for language in WhatsAppMessageTemplatesLanguages
        ]

        return Response({"languages": all_languages}, status=status.HTTP_200_OK)


class WhatsappIntegrationWebhookView(APIView):
    permission_classes = [InternalAuthenticationPermission]

    @extend_schema(
        request=WhatsappIntegrationWebhookSerializer,
        responses={status.HTTP_204_NO_CONTENT: None},
    )
    def post(self, request: Request) -> Response:
        serializer = WhatsappIntegrationWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = Project.objects.get(uuid=serializer.validated_data["project_uuid"])

        config = {
            "is_whatsapp_integration": True,
            "waba_id": serializer.validated_data["waba_id"],
            "phone_number": serializer.validated_data["phone_number"],
            "app_uuid": str(serializer.validated_data["app_uuid"]),
        }

        existing_dashboard = Dashboard.objects.filter(
            project=project,
            config__waba_id=serializer.validated_data["waba_id"],
            config__is_whatsapp_integration=True,
        ).first()

        if existing_dashboard:
            existing_dashboard.config = config
            existing_dashboard.save(update_fields=["config"])

        else:
            name = f"Meta {serializer.validated_data['phone_number']['display_phone_number']}"

            Dashboard.objects.create(
                project=project,
                config=config,
                name=name,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        request=WhatsappIntegrationWebhookRemoveSerializer,
        responses={status.HTTP_204_NO_CONTENT: None},
    )
    def delete(self, request: Request) -> Response:
        serializer = WhatsappIntegrationWebhookRemoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        Dashboard.objects.filter(
            project__uuid=serializer.validated_data["project_uuid"],
            config__waba_id=serializer.validated_data["waba_id"],
        ).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
