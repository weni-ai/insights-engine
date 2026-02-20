import json
import logging

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import GenericViewSet
from sentry_sdk import capture_exception

from insights.authentication.permissions import (
    InternalAuthenticationPermission,
    ProjectAuthQueryParamPermission,
)
from insights.dashboards.models import Dashboard
from insights.metrics.meta.choices import (
    WhatsAppMessageTemplatesCategories,
    WhatsAppMessageTemplatesLanguages,
)
from insights.metrics.meta.enums import ProductType
from insights.metrics.meta.models import FavoriteTemplate
from insights.metrics.meta.permissions import ProjectDashboardWABAPermission
from insights.metrics.meta.schema import (
    WHATSAPP_MESSAGE_TEMPLATES_GENERAL_PARAMS,
    WHATSAPP_MESSAGE_TEMPLATES_LIST_TEMPLATES_PARAMS,
    WHATSAPP_MESSAGE_TEMPLATES_MSGS_ANALYTICS_PARAMS,
)
from insights.metrics.meta.serializers import (
    ConversationsByCategoryQueryParamsSerializer,
    TemplatesMetricsAnalyticsBodySerializer,
    TemplatesMetricsAnalyticsQueryParamsSerializer,
    WhatsappIntegrationWebhookRemoveSerializer,
    AddTemplateToFavoritesSerializer,
    FavoriteTemplatesQueryParamsSerializer,
    FavoriteTemplatesSerializer,
    MessageTemplatesCategoriesSerializer,
    MessageTemplatesLanguagesSerializer,
    MessageTemplatesQueryParamsSerializer,
    RemoveTemplateFromFavoritesSerializer,
    WabaSerializer,
    WhatsappIntegrationWebhookSerializer,
)
from insights.metrics.meta.services import MetaMessageTemplatesService
from insights.metrics.meta.utils import (
    get_edit_template_url_from_template_data,
)
from insights.projects.models import Project
from insights.sources.integrations.clients import WeniIntegrationsClient

logger = logging.getLogger(__name__)


class WhatsAppMessageTemplatesView(GenericViewSet):
    service = MetaMessageTemplatesService()
    permission_classes = [
        IsAuthenticated,
        ProjectAuthQueryParamPermission,
        ProjectDashboardWABAPermission,
    ]

    @property
    def project_uuid_field(self):
        """Set project_uuid_field based on the action"""
        action_field_map = {
            "get_conversations_by_category": "project",
        }
        return action_field_map.get(self.action, "project_uuid")

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

        data = self.service.get_templates_list(filters=serializer.validated_data)

        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(parameters=WHATSAPP_MESSAGE_TEMPLATES_GENERAL_PARAMS)
    @action(detail=False, methods=["get"], url_name="preview", url_path="preview")
    def preview_template(self, request: Request) -> Response:
        data = self.service.get_template_preview(filters=request.query_params)

        waba_id = request.query_params.get("waba_id")
        template_id = request.query_params.get("template_id")

        is_favorite = FavoriteTemplate.objects.filter(
            dashboard__config__waba_id=waba_id, template_id=template_id
        ).exists()

        project_uuid = request.query_params.get("project_uuid")
        edit_template_url = get_edit_template_url_from_template_data(
            project_uuid, template_id
        )

        data = {
            "is_favorite": is_favorite,
            "edit_template_url": edit_template_url,
            **data,
        }

        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(parameters=WHATSAPP_MESSAGE_TEMPLATES_MSGS_ANALYTICS_PARAMS)
    @action(
        detail=False,
        methods=["get"],
        url_name="messages-analytics",
        url_path="messages-analytics",
    )
    def messages_analytics(self, request: Request) -> Response:
        project_uuid = self.request.query_params.get("project_uuid")

        project = Project.objects.filter(uuid=project_uuid).first()
        timezone = project.timezone if project else None

        data = self.service.get_messages_analytics(
            filters=request.query_params, timezone_name=timezone
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
        project_uuid = self.request.query_params.get("project_uuid")

        project = Project.objects.filter(uuid=project_uuid).first()
        timezone = project.timezone if project else None

        data = self.service.get_buttons_analytics(
            filters=request.query_params, timezone_name=timezone
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

        template_preview = self.service.get_template_preview(filters=preview_filters)
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

    @extend_schema(responses={status.HTTP_200_OK: WabaSerializer(many=True)})
    @action(
        detail=False,
        methods=["get"],
        url_name="wabas",
        url_path="wabas",
        permission_classes=[IsAuthenticated, ProjectAuthQueryParamPermission],
    )
    def wabas(self, request: Request) -> Response:
        project_uuid = request.query_params.get("project_uuid")

        # Staging only:
        dashboards = Dashboard.objects.filter(
            project_uuid=project_uuid, config__is_whatsapp_integration=True
        )
        wabas_data = []

        for dashboard in dashboards:
            config = dashboard.config or {}
            wabas_data.append(
                {
                    "id": config.get("waba_id"),
                    "phone_number": config.get("phone_number").get(
                        "display_phone_number"
                    ),
                }
            )

        return Response(
            {"results": WabaSerializer(wabas_data, many=True).data},
            status=status.HTTP_200_OK,
        )

        try:
            wabas_data = WeniIntegrationsClient().get_wabas_for_project(project_uuid)
        except ValueError as e:
            capture_exception(e)
            logger.error(
                "Error fetching wabas for project %s: %s",
                project_uuid,
                e,
            )
            return Response(
                {"error": "Error fetching wabas"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"results": WabaSerializer(wabas_data, many=True).data},
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["get"],
        url_name="conversations-by-category",
        url_path="conversations-by-category",
    )
    def get_conversations_by_category(self, request: Request) -> Response:
        serializer = ConversationsByCategoryQueryParamsSerializer(
            data=request.query_params
        )
        serializer.is_valid(raise_exception=True)

        categories_data = self.service.get_conversations_by_category(
            waba_id=serializer.validated_data["waba_id"],
            start_date=serializer.validated_data["start_date"],
            end_date=serializer.validated_data["end_date"],
        )

        return Response({"templates": categories_data}, status=status.HTTP_200_OK)


class WhatsappIntegrationWebhookView(APIView):
    permission_classes = [InternalAuthenticationPermission]

    @extend_schema(
        request=WhatsappIntegrationWebhookSerializer,
        responses={status.HTTP_204_NO_CONTENT: None},
    )
    def post(self, request: Request) -> Response:
        serializer = WhatsappIntegrationWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            project = Project.objects.get(
                uuid=serializer.validated_data["project_uuid"]
            )

            config = {
                "is_whatsapp_integration": True,
                "app_uuid": str(serializer.validated_data["app_uuid"]),
                "waba_id": serializer.validated_data["waba_id"],
                "phone_number": serializer.validated_data["phone_number"],
            }

            existing_dashboard = Dashboard.objects.filter(
                project=project,
                config__phone_number__id=serializer.validated_data["phone_number"][
                    "id"
                ],
                config__is_whatsapp_integration=True,
            ).first()

            if existing_dashboard:
                existing_dashboard.config = config
                existing_dashboard.save(update_fields=["config"])

            else:
                name = f"Meta {serializer.validated_data['phone_number']['display_phone_number']}"

                existing_dashboard = Dashboard.objects.create(
                    project=project,
                    config=config,
                    name=name,
                )

            current_project = existing_dashboard.project

            main_project = Project.objects.filter(
                org_uuid=current_project.org_uuid,
                config__is_main_project=True,
            ).first()

            if main_project:
                # Create a copy of this dashboard in the main project
                name = f"{current_project.name} {serializer.validated_data['phone_number']['display_phone_number']}"
                Dashboard.objects.create(
                    project=main_project,
                    config=config,
                    name=name,
                )

        except Exception as e:
            logger.exception(f"Database error in WhatsApp integration: {e}")
            return Response(
                {"error": "Failed to save integration"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        request=WhatsappIntegrationWebhookRemoveSerializer,
        responses={status.HTTP_204_NO_CONTENT: None},
    )
    def delete(self, request: Request) -> Response:
        serializer = WhatsappIntegrationWebhookRemoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        current_project = Project.objects.filter(
            uuid=serializer.validated_data["project_uuid"],
        ).first()

        projects = [current_project]

        main_project = Project.objects.filter(
            org_uuid=current_project.org_uuid,
            config__is_main_project=True,
        ).first()

        if main_project:
            projects.append(main_project)

        try:
            Dashboard.objects.filter(
                project__in=projects,
                config__waba_id=serializer.validated_data["waba_id"],
            ).delete()
        except Exception as e:
            logger.exception(f"Database error removing WhatsApp integration: {e}")
            return Response(
                {"error": "Failed to remove integration"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class InternalWhatsAppMessageTemplatesView(GenericViewSet):
    permission_classes = [InternalAuthenticationPermission]
    service = MetaMessageTemplatesService()

    @action(
        detail=False,
        methods=["post"],
        url_name="messages-analytics",
        url_path="messages-analytics",
    )
    def messages_analytics(self, request: Request) -> Response:
        errors = {}

        try:
            query_params_serializer = TemplatesMetricsAnalyticsQueryParamsSerializer(
                data=request.query_params
            )
            query_params_serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            errors["query_params"] = e.detail

        try:
            body_serializer = TemplatesMetricsAnalyticsBodySerializer(data=request.data)
            body_serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            errors["body"] = e.detail

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        filters = {
            "waba_id": query_params_serializer.validated_data["waba_id"],
            "start_date": query_params_serializer.validated_data["start_date"],
            "end_date": query_params_serializer.validated_data["end_date"],
            "template_id": body_serializer.validated_data["template_ids"],
            "product_type": body_serializer.validated_data.get("product_type")
            or ProductType.CLOUD_API.value,
        }

        data = self.service.get_messages_analytics(
            filters=filters,
            skip_kwargs_validation=True,
            include_data_points=False,
            # Returning the original exceptions because this is an internal endpoint
            return_exceptions=True,
        )

        return Response(data, status=status.HTTP_200_OK)
