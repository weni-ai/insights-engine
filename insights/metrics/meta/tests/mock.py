MOCK_TEMPLATES_LIST_BODY = {
    "data": [
        {
            "name": "example",
            "parameter_format": "POSITIONAL",
            "components": [
                {
                    "type": "BODY",
                    "text": "Hello, {{1}}, this is an example",
                    "example": {
                        "body_text": [
                            [
                                "Jane",
                            ]
                        ]
                    },
                },
                {
                    "type": "BUTTONS",
                    "buttons": [
                        {"type": "QUICK_REPLY", "text": "Continue"},
                        {"type": "QUICK_REPLY", "text": "Cancel"},
                    ],
                },
            ],
            "language": "en_US",
            "status": "APPROVED",
            "category": "MARKETING",
            "id": "123456789098765",
        },
        {
            "name": "example_2",
            "parameter_format": "POSITIONAL",
            "components": [
                {
                    "type": "BODY",
                    "text": "Hello, {{1}}, this is another example",
                    "example": {
                        "body_text": [
                            [
                                "Jane",
                            ]
                        ]
                    },
                },
                {
                    "type": "BUTTONS",
                    "buttons": [
                        {"type": "QUICK_REPLY", "text": "Continue"},
                        {"type": "QUICK_REPLY", "text": "Cancel"},
                    ],
                },
            ],
            "language": "en_US",
            "status": "APPROVED",
            "category": "MARKETING",
            "id": "123456789098767",
        },
    ]
}

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
                {
                    "type": "URL",
                    "text": "Access service",
                    "url": "https://example.local/",
                }
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
                    "sent": 10,
                    "delivered": 8,
                    "read": 6,
                    "clicked": [
                        {
                            "type": "quick_reply_button",
                            "button_content": "Access service",
                            "count": 2,
                        },
                    ],
                },
                {
                    "template_id": "123456789098765",
                    "start": 1733097600,
                    "end": 1733184000,
                    "sent": 5,
                    "delivered": 4,
                    "read": 3,
                    "clicked": [
                        {
                            "type": "quick_reply_button",
                            "button_content": "Access service",
                            "count": 1,
                        },
                    ],
                },
            ],
        }
    ],
    "paging": {"cursors": {"before": "ZNSKLL", "after": "NJAPQOOQZ"}},
}


MOCK_TEMPLATE_DAILY_ANALYTICS_INVALID_PERIOD = {
    "error": {
        "message": "Invalid parameter",
        "type": "OAuthException",
        "code": 100,
        "error_data": "Invalid start and end times. End time requested is before start time.",
        "error_subcode": 4182001,
        "is_transient": False,
        "error_user_title": "Horas de início e de término incorretas",
        "error_user_msg": "Start time must be earlier than end time.",
        "fbtrace_id": "XLZSJnaBAvqHAVkqlappqAK",
    }
}
