import pytest
from clients import VtexOrdersRestClient
from unittest.mock import patch, Mock
import json


@pytest.mark.django_db
@patch("clients.VtexOrdersRestClient.list")
def test_verify_fields(mock_list):
    mock_list.return_value = {
        "countSell": 1,
        "accumulatedTotal": 50.21,
        "ticketMax": 50.21,
        "ticketMin": 50.21,
        "medium_ticket": 50.21,
    }
    client = VtexOrdersRestClient()
    query_filters = {
        "start_date": "2024-09-01T00:00:00.000Z",
        "end_date": "2024-09-04T00:00:00.000Z",
        "base_url": "gbarbosa",
        "utm_source": "gbarbosa-recuperacaochatbotvtex",
    }
    response = client.list(query_filters)
    expected_keys = {
        "countSell",
        "accumulatedTotal",
        "ticketMax",
        "ticketMin",
        "medium_ticket",
    }
    assert set(response.keys()) == expected_keys


@pytest.mark.django_db
def test_missing_utm_source():
    client = VtexOrdersRestClient()

    query_filters = {
        "start_date": "2024-09-01T00:00:00.000Z",
        "end_date": "2024-09-04T00:00:00.000Z",
        "base_url": "gbarbosa",
    }

    response = client.list(query_filters)

    assert response == {"error": "utm_source field is mandatory"}


@pytest.mark.django_db
def test_cache_behavior():
    client = VtexOrdersRestClient()
    cached_response = {
        "countSell": 1,
        "accumulatedTotal": 50.21,
        "ticketMax": 50.21,
        "ticketMin": 50.21,
        "medium_ticket": 50.21,
    }

    client.cache = Mock()
    client.cache.get.return_value = json.dumps(cached_response)

    query_filters = {
        "start_date": "2024-09-01T00:00:00.000Z",
        "end_date": "2024-09-04T00:00:00.000Z",
        "base_url": "gbarbosa",
        "utm_source": "gbarbosa-recuperacaochatbotvtex",
    }

    response = client.list(query_filters)
    assert response == (200, cached_response)
    client.cache.get.assert_called_once_with(client.get_cache_key(query_filters))
