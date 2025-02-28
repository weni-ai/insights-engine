from drf_spectacular.openapi import OpenApiParameter


WHATSAPP_MESSAGE_TEMPLATES_LIST_TEMPLATES_PARAMS = [
    OpenApiParameter(
        name="project_uuid",
        type=str,
        location=OpenApiParameter.QUERY,
        required=True,
    ),
    OpenApiParameter(
        name="waba_id",
        type=str,
        location=OpenApiParameter.QUERY,
        required=True,
    ),
]

WHATSAPP_MESSAGE_TEMPLATES_GENERAL_PARAMS = [
    OpenApiParameter(
        name="project_uuid",
        type=str,
        location=OpenApiParameter.QUERY,
        required=True,
    ),
    OpenApiParameter(
        name="waba_id",
        type=str,
        location=OpenApiParameter.QUERY,
        required=True,
    ),
    OpenApiParameter(
        name="template_id",
        type=str,
        location=OpenApiParameter.QUERY,
        required=True,
    ),
]

WHATSAPP_MESSAGE_TEMPLATES_MSGS_ANALYTICS_PARAMS = (
    WHATSAPP_MESSAGE_TEMPLATES_GENERAL_PARAMS
    + [
        OpenApiParameter(
            name="start_date",
            type=str,
            location=OpenApiParameter.QUERY,
            required=True,
            description="Date in YYYY-MM-DD format",
        ),
        OpenApiParameter(
            name="end_date",
            type=str,
            location=OpenApiParameter.QUERY,
            required=True,
            description="Date in YYYY-MM-DD format",
        ),
    ]
)
