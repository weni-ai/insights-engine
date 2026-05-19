MOCK_INTEGRATED_FEATURES_WITH_CART = {
    "results": [
        {
            "uuid": "b80555f9-110d-4893-8d4e-661c6b349611",
            "feature_uuid": "6e614fc2-8702-435c-b479-7bffd587fcee",
            "code": "abandoned_cart",
            "name": "Opinionated Abandoned Cart",
        }
    ]
}

MOCK_INTEGRATED_FEATURES_WITHOUT_CART = {
    "results": [
        {
            "uuid": "b80555f9-110d-4893-8d4e-661c6b349611",
            "feature_uuid": "6e614fc2-8702-435c-b479-7bffd587fcee",
            "code": "something_else",
            "name": "Other Feature",
        }
    ]
}

MOCK_INTEGRATED_FEATURES_EMPTY = {"results": []}


MOCK_AGENTS_WITH_LEGACY_CART = {
    "gallery_agents": [
        {
            "slug": "active_cart_abandonment",
            "assigned": True,
        }
    ]
}

MOCK_AGENTS_WITH_LEGACY_CART_NOT_ASSIGNED = {
    "gallery_agents": [
        {
            "slug": "active_cart_abandonment",
            "assigned": False,
        }
    ]
}

MOCK_AGENTS_WITHOUT_LEGACY_CART = {
    "gallery_agents": [
        {
            "slug": "another_agent",
            "assigned": True,
        }
    ]
}


MOCK_META_PRICING_RESPONSE = {
    "source": "contract",
    "currency": "BRL",
    "rates": {
        "marketing": "0.5",
        "utility": "0",
        "service": "0",
        "authentication": "0",
    },
}
