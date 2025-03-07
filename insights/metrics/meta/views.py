from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.views import APIView

from insights.authentication.permissions import (
    InternalAuthenticationPermission,
    ProjectAuthQueryParamPermission,
)
from insights.dashboards.models import Dashboard
from insights.metrics.meta.permissions import ProjectWABAPermission
from insights.metrics.meta.schema import (
    WHATSAPP_MESSAGE_TEMPLATES_GENERAL_PARAMS,
    WHATSAPP_MESSAGE_TEMPLATES_LIST_TEMPLATES_PARAMS,
    WHATSAPP_MESSAGE_TEMPLATES_MSGS_ANALYTICS_PARAMS,
)
from insights.projects.models import Project
from insights.metrics.meta.serializers import (
    WhatsappIntegrationWebhookRemoveSerializer,
    MessageTemplatesQueryParamsSerializer,
    WhatsappIntegrationWebhookSerializer,
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
            name = f"Meta - {serializer.validated_data['phone_number']['display_phone_number']}"

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
