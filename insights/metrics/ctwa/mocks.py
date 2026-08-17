MOCK_CURRENCY = "USD"
MOCK_ORGANIC_CONVERSATIONS = 22800

MOCK_CAMPAIGNS_PERFORMANCE = [
    {
        "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "campaign": "Contractor Bulk Pricing",
        "conversations": 3200,
        "qualified": 1450,
        "conversions": 520,
        "revenue": 509600,
    },
    {
        "uuid": "b2c3d4e5-f678-9012-bcde-f12345678901",
        "campaign": "Pro Account Signup",
        "conversations": 2100,
        "qualified": 780,
        "conversions": 210,
        "revenue": 134400,
    },
    {
        "uuid": "c3d4e5f6-7890-1234-cdef-123456789012",
        "campaign": "Weekend DIY Deals",
        "conversations": 7400,
        "qualified": 2650,
        "conversions": 1180,
        "revenue": 212400,
    },
    {
        "uuid": "d4e5f678-9012-3456-defa-234567890123",
        "campaign": "New Store Opening",
        "conversations": 4100,
        "qualified": 1180,
        "conversions": 430,
        "revenue": 64500,
    },
    {
        "uuid": "e5f67890-1234-5678-efab-345678901234",
        "campaign": "Black friday",
        "conversations": 2600,
        "qualified": 1120,
        "conversions": 540,
        "revenue": 113400,
    },
]

MOCK_CAMPAIGNS = [
    {"name": campaign["campaign"], "uuid": campaign["uuid"]}
    for campaign in MOCK_CAMPAIGNS_PERFORMANCE
]


def filter_campaigns(campaign_uuid: str | None = None) -> list[dict]:
    if not campaign_uuid:
        return MOCK_CAMPAIGNS_PERFORMANCE
    campaign_uuid = str(campaign_uuid)
    return [
        campaign
        for campaign in MOCK_CAMPAIGNS_PERFORMANCE
        if campaign["uuid"] == campaign_uuid
    ]


def aggregate_campaigns(campaign_uuid: str | None = None) -> dict:
    rows = filter_campaigns(campaign_uuid)
    conversations = sum(row["conversations"] for row in rows)
    qualified = sum(row["qualified"] for row in rows)
    conversions = sum(row["conversions"] for row in rows)
    revenue = sum(row["revenue"] for row in rows)

    return {
        "conversations": conversations,
        "qualified": qualified,
        "conversions": conversions,
        "revenue": revenue,
        "avg": round(revenue / conversions) if conversions else 0,
    }
