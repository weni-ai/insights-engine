from unittest.mock import MagicMock

from django.test import TestCase

from insights.core.urls.proxy_pagination import (
    get_cursor_based_pagination_urls,
    get_limit_offset_pagination_urls,
)


def _make_request(url: str) -> MagicMock:
    request = MagicMock()
    request.build_absolute_uri.return_value = url
    return request


class GetCursorBasedPaginationURLsTestCase(TestCase):
    def test_both_next_and_previous(self):
        request = _make_request(
            "https://insights.example.com/api/messages/?page_size=10&cursor=abc"
        )
        response_body = {
            "next": "https://upstream.service.com/messages/?cursor=next123&page_size=10",
            "previous": "https://upstream.service.com/messages/?cursor=prev456&page_size=10",
        }

        result = get_cursor_based_pagination_urls(request, response_body)

        self.assertIn("cursor=next123", result.next_url)
        self.assertIn("page_size=10", result.next_url)
        self.assertTrue(
            result.next_url.startswith("https://insights.example.com/api/messages/")
        )

        self.assertIn("cursor=prev456", result.previous_url)
        self.assertIn("page_size=10", result.previous_url)
        self.assertTrue(
            result.previous_url.startswith(
                "https://insights.example.com/api/messages/"
            )
        )

    def test_only_next(self):
        request = _make_request(
            "https://insights.example.com/api/messages/?page_size=5"
        )
        response_body = {
            "next": "https://upstream.service.com/messages/?cursor=next789&page_size=5",
            "previous": None,
        }

        result = get_cursor_based_pagination_urls(request, response_body)

        self.assertIn("cursor=next789", result.next_url)
        self.assertIn("page_size=5", result.next_url)
        self.assertIsNone(result.previous_url)

    def test_only_previous(self):
        request = _make_request(
            "https://insights.example.com/api/messages/?page_size=5&cursor=cur1"
        )
        response_body = {
            "next": None,
            "previous": "https://upstream.service.com/messages/?cursor=prev111&page_size=5",
        }

        result = get_cursor_based_pagination_urls(request, response_body)

        self.assertIsNone(result.next_url)
        self.assertIn("cursor=prev111", result.previous_url)
        self.assertIn("page_size=5", result.previous_url)

    def test_neither_next_nor_previous(self):
        request = _make_request(
            "https://insights.example.com/api/messages/?page_size=10"
        )
        response_body = {"next": None, "previous": None}

        result = get_cursor_based_pagination_urls(request, response_body)

        self.assertIsNone(result.next_url)
        self.assertIsNone(result.previous_url)

    def test_preserves_extra_query_params(self):
        request = _make_request(
            "https://insights.example.com/api/messages/?page_size=10&project=proj1&cursor=old"
        )
        response_body = {
            "next": "https://upstream.service.com/messages/?cursor=nxt&page_size=10",
            "previous": None,
        }

        result = get_cursor_based_pagination_urls(request, response_body)

        self.assertIn("project=proj1", result.next_url)
        self.assertIn("cursor=nxt", result.next_url)

    def test_custom_param_names(self):
        request = _make_request(
            "https://insights.example.com/api/items/?ps=20&c=abc"
        )
        response_body = {
            "next": "https://upstream.service.com/items/?c=next_c&ps=20",
            "previous": None,
        }

        result = get_cursor_based_pagination_urls(
            request, response_body, page_size_param="ps", cursor_param="c"
        )

        self.assertIn("c=next_c", result.next_url)
        self.assertIn("ps=20", result.next_url)
        self.assertIsNone(result.previous_url)

    def test_no_page_size_in_request(self):
        request = _make_request(
            "https://insights.example.com/api/messages/"
        )
        response_body = {
            "next": "https://upstream.service.com/messages/?cursor=nxt",
            "previous": None,
        }

        result = get_cursor_based_pagination_urls(request, response_body)

        self.assertIn("cursor=nxt", result.next_url)
        self.assertNotIn("page_size", result.next_url)

    def test_response_without_cursor_in_upstream_next(self):
        request = _make_request(
            "https://insights.example.com/api/messages/?page_size=10"
        )
        response_body = {
            "next": "https://upstream.service.com/messages/?page_size=10",
            "previous": None,
        }

        result = get_cursor_based_pagination_urls(request, response_body)

        self.assertIsNotNone(result.next_url)
        self.assertNotIn("cursor=", result.next_url)
        self.assertIn("page_size=10", result.next_url)


class GetLimitOffsetPaginationURLsTestCase(TestCase):
    def test_both_next_and_previous(self):
        request = _make_request(
            "https://insights.example.com/api/items/?limit=10&offset=20"
        )
        response_body = {
            "next": "https://upstream.service.com/items/?limit=10&offset=30",
            "previous": "https://upstream.service.com/items/?limit=10&offset=10",
        }

        result = get_limit_offset_pagination_urls(request, response_body)

        self.assertIn("limit=10", result.next_url)
        self.assertIn("offset=30", result.next_url)
        self.assertTrue(
            result.next_url.startswith("https://insights.example.com/api/items/")
        )

        self.assertIn("limit=10", result.previous_url)
        self.assertIn("offset=10", result.previous_url)
        self.assertTrue(
            result.previous_url.startswith("https://insights.example.com/api/items/")
        )

    def test_only_next(self):
        request = _make_request(
            "https://insights.example.com/api/items/?limit=5&offset=0"
        )
        response_body = {
            "next": "https://upstream.service.com/items/?limit=5&offset=5",
            "previous": None,
        }

        result = get_limit_offset_pagination_urls(request, response_body)

        self.assertIn("limit=5", result.next_url)
        self.assertIn("offset=5", result.next_url)
        self.assertIsNone(result.previous_url)

    def test_only_previous(self):
        request = _make_request(
            "https://insights.example.com/api/items/?limit=10&offset=10"
        )
        response_body = {
            "next": None,
            "previous": "https://upstream.service.com/items/?limit=10&offset=0",
        }

        result = get_limit_offset_pagination_urls(request, response_body)

        self.assertIsNone(result.next_url)
        self.assertIn("limit=10", result.previous_url)
        self.assertIn("offset=0", result.previous_url)

    def test_neither_next_nor_previous(self):
        request = _make_request(
            "https://insights.example.com/api/items/?limit=10&offset=0"
        )
        response_body = {"next": None, "previous": None}

        result = get_limit_offset_pagination_urls(request, response_body)

        self.assertIsNone(result.next_url)
        self.assertIsNone(result.previous_url)

    def test_preserves_extra_query_params(self):
        request = _make_request(
            "https://insights.example.com/api/items/?limit=10&offset=0&status=active"
        )
        response_body = {
            "next": "https://upstream.service.com/items/?limit=10&offset=10",
            "previous": None,
        }

        result = get_limit_offset_pagination_urls(request, response_body)

        self.assertIn("status=active", result.next_url)
        self.assertIn("limit=10", result.next_url)
        self.assertIn("offset=10", result.next_url)

    def test_custom_param_names(self):
        request = _make_request(
            "https://insights.example.com/api/items/?l=20&o=40"
        )
        response_body = {
            "next": "https://upstream.service.com/items/?l=20&o=60",
            "previous": "https://upstream.service.com/items/?l=20&o=20",
        }

        result = get_limit_offset_pagination_urls(
            request, response_body, limit_param="l", offset_param="o"
        )

        self.assertIn("l=20", result.next_url)
        self.assertIn("o=60", result.next_url)
        self.assertIn("l=20", result.previous_url)
        self.assertIn("o=20", result.previous_url)

    def test_upstream_previous_without_offset(self):
        request = _make_request(
            "https://insights.example.com/api/items/?limit=10&offset=10"
        )
        response_body = {
            "next": None,
            "previous": "https://upstream.service.com/items/?limit=10",
        }

        result = get_limit_offset_pagination_urls(request, response_body)

        self.assertIsNotNone(result.previous_url)
        self.assertNotIn("offset=", result.previous_url)
        self.assertIn("limit=10", result.previous_url)
