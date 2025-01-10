MOCK_SUCCESS_RESPONSE_BODY = {
    "name": "testing",
    "parameter_format": "POSITIONAL",
    "components": [
        {"type": "HEADER", "format": "TEXT", "text": "Test"},
        {
            "type": "HEADER",
            "format": "IMAGE",
            "example": {
                "header_handle": [
                    "https://scontent.whatsapp.net/v/t61.29466-34/123456789_123456789876543_1234567891234567898_n.png"
                ]
            },
        },
        {
            "type": "BODY",
            "text": "Just testing",
            "example": {"body_text": [["test"]]},
        },
        {
            "type": "BUTTONS",
            "buttons": [
                {"type": "URL", "text": "link", "url": "https://example.local/"}
            ],
        },
    ],
    "language": "en_US",
    "status": "APPROVED",
    "category": "MARKETING",
    "id": "1234567890987654",
}

MOCK_ERROR_RESPONSE_BODY = {
    "error": {
        "message": "Unsupported get request. Object with ID '1234567890987654' does not exist, cannot be loaded due to missing permissions, or does not support this operation. Please read the Graph API documentation at https://developers.facebook.com/docs/graph-api",
        "type": "GraphMethodException",
        "code": 100,
        "error_subcode": 33,
        "fbtrace_id": "fjXJSSiOahsAHSshASQEOEQ",
    }
}

MOCK_TEMPLATE_DAILY_ANALYTICS = {
    "data": [
        {
            "granularity": "DAILY",
            "product_type": "cloud_api",
            "data_points": [
                {
                    "template_id": "123456789098765",
                    "start": 1733011200,
                    "end": 1733097600,
                    "sent": 0,
                    "delivered": 0,
                    "read": 0,
                },
                {
                    "template_id": "123456789098765",
                    "start": 1733097600,
                    "end": 1733184000,
                    "sent": 0,
                    "delivered": 0,
                    "read": 0,
                },
            ],
        }
    ],
    "paging": {"cursors": {"before": "ZNSKLL", "after": "NJAPQOOQZ"}},
}
