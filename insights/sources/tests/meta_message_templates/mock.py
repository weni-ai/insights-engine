MOCK_SUCCESS_RESPONSE_BODY = {
    "name": "testing",
    "parameter_format": "POSITIONAL",
    "components": [
        {"type": "HEADER", "format": "TEXT", "text": "Test"},
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
