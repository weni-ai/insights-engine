import json
from unittest.mock import MagicMock, patch
from django.test import TestCase
from insights.sources.orders.clients import VtexOrdersRestClient
from insights.sources.cache import CacheClient
from datetime import datetime, timezone, timedelta
from concurrent.futures import Future


class TestVtexOrdersRestClient(TestCase):
    def setUp(self):
        self.auth_params_direct = {
            "domain": "testenv",
            "app_token": "test_token",
            "app_key": "test_key",
            "internal_token": "internal_token_test",
        }
        self.auth_params_io_proxy = {
            "domain": "testenv.myvtex.com",
            "internal_token": "internal_token_test",
        }
        self.mock_cache_client = MagicMock(spec=CacheClient)
        self.client_direct = VtexOrdersRestClient(
            auth_params=self.auth_params_direct,
            cache_client=self.mock_cache_client,
            use_io_proxy=False,
        )
        self.client_io_proxy = VtexOrdersRestClient(
            auth_params=self.auth_params_io_proxy,
            cache_client=self.mock_cache_client,
            use_io_proxy=True,
        )

    def test_initialization_direct(self):
        self.assertEqual(self.client_direct.base_url, "testenv")
        self.assertFalse(self.client_direct.use_io_proxy)
        self.assertEqual(
            self.client_direct.headers,
            {
                "X-VTEX-API-AppToken": "test_token",
                "X-VTEX-API-AppKey": "test_key",
            },
        )
        self.assertEqual(self.client_direct.cache, self.mock_cache_client)

    def test_initialization_io_proxy(self):
        self.assertEqual(self.client_io_proxy.base_url, "https://testenv.myvtex.com")
        self.assertTrue(self.client_io_proxy.use_io_proxy)
        self.assertEqual(
            self.client_io_proxy.headers,
            {"X-Weni-Auth": "internal_token_test"},
        )
        self.assertEqual(self.client_io_proxy.cache, self.mock_cache_client)

    def test_initialization_io_proxy_with_https_and_myvtex(self):
        auth_params_custom = {
            "domain": "https://another.myvtex.com",
            "internal_token": "internal_token_test",
        }
        client = VtexOrdersRestClient(
            auth_params=auth_params_custom,
            cache_client=self.mock_cache_client,
            use_io_proxy=True,
        )
        self.assertEqual(client.base_url, "https://another.myvtex.com")

    def test_initialization_io_proxy_without_https_and_myvtex(self):
        auth_params_custom = {
            "domain": "justdomain",
            "internal_token": "internal_token_test",
        }
        client = VtexOrdersRestClient(
            auth_params=auth_params_custom,
            cache_client=self.mock_cache_client,
            use_io_proxy=True,
        )
        self.assertEqual(client.base_url, "https://justdomain.myvtex.com")

    def test_get_cache_key(self):
        query_filters = {"param1": "value1", "param2": "value2"}
        expected_key = f"vtex_data:{json.dumps(query_filters, sort_keys=True)}"
        self.assertEqual(self.client_direct.get_cache_key(query_filters), expected_key)

    def test_get_query_params(self):
        query_filters = {
            "ended_at__gte": "2023-01-01T00:00:00Z",
            "ended_at__lte": "2023-01-31T23:59:59Z",
            "utm_source": "test_source",
        }
        page_number = 1
        expected_params = {
            "f_UtmSource": "test_source",
            "per_page": 100,
            "page": page_number,
            "f_status": "invoiced",
            "f_authorizedDate": "authorizedDate:[2023-01-01T00:00:00Z TO 2023-01-31T23:59:59Z]",
        }
        self.assertEqual(
            self.client_direct.get_query_params(query_filters, page_number),
            expected_params,
        )

    def test_get_query_params_no_dates(self):
        query_filters = {"utm_source": "test_source"}
        page_number = 2
        expected_params = {
            "f_UtmSource": "test_source",
            "per_page": 100,
            "page": page_number,
            "f_status": "invoiced",
        }
        self.assertEqual(
            self.client_direct.get_query_params(query_filters, page_number),
            expected_params,
        )

    def test_get_vtex_endpoint_direct(self):
        query_filters = {"utm_source": "test_source"}
        page_number = 1
        # Manually construct the expected URL because urlencode might order params differently
        # but the functional result is the same.
        actual_url = self.client_direct.get_vtex_endpoint(query_filters, page_number)
        self.assertTrue(actual_url.startswith("testenv/api/oms/pvt/orders/?"))
        self.assertIn("f_UtmSource=test_source", actual_url)
        self.assertIn("per_page=100", actual_url)
        self.assertIn("page=1", actual_url)
        self.assertIn("f_status=invoiced", actual_url)

    def test_get_vtex_endpoint_io_proxy(self):
        query_filters = {"utm_source": "test_source"}
        page_number = 1
        expected_url = "https://testenv.myvtex.com/_v/orders/"
        self.assertEqual(
            self.client_io_proxy.get_vtex_endpoint(query_filters, page_number),
            expected_url,
        )

    def test_get_request_body_direct(self):
        query_filters = {"utm_source": "test_source"}
        page_number = 1
        self.assertEqual(
            self.client_direct.get_request_body(query_filters, page_number), {}
        )

    def test_get_request_body_io_proxy(self):
        query_filters = {"utm_source": "test_source_proxy"}
        page_number = 3
        expected_body = {
            "raw_query": {
                "f_UtmSource": "test_source_proxy",
                "per_page": 100,
                "page": page_number,
                "f_status": "invoiced",
            }
        }
        self.assertEqual(
            self.client_io_proxy.get_request_body(query_filters, page_number),
            expected_body,
        )

    @patch("insights.sources.orders.clients.requests.get")
    def test_get_orders_list_direct_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"list": [], "paging": {"pages": 1}}
        mock_get.return_value = mock_response

        query_filters = {"utm_source": "test"}
        page_number = 1
        response = self.client_direct.get_orders_list(query_filters, page_number)

        self.assertTrue(response.ok)
        mock_get.assert_called_once()
        # We can add more assertions about the URL and headers if needed

    @patch("insights.sources.orders.clients.requests.get")
    @patch("insights.sources.orders.clients.capture_message")
    def test_get_orders_list_direct_error(self, mock_capture_message, mock_get):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        mock_get.return_value = mock_response

        query_filters = {"utm_source": "test"}
        page_number = 1
        response = self.client_direct.get_orders_list(query_filters, page_number)

        self.assertFalse(response.ok)
        mock_get.assert_called_once()
        mock_capture_message.assert_called_once()

    @patch("insights.sources.orders.clients.requests.post")
    def test_get_orders_list_io_proxy_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"list": [], "paging": {"pages": 1}}
        mock_post.return_value = mock_response

        query_filters = {"utm_source": "test_proxy"}
        page_number = 1
        response = self.client_io_proxy.get_orders_list(query_filters, page_number)

        self.assertTrue(response.ok)
        mock_post.assert_called_once()
        # We can add more assertions about the URL, headers and json body if needed

    @patch("insights.sources.orders.clients.requests.post")
    @patch("insights.sources.orders.clients.capture_message")
    def test_get_orders_list_io_proxy_error(self, mock_capture_message, mock_post):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        query_filters = {"utm_source": "test_proxy"}
        page_number = 1
        response = self.client_io_proxy.get_orders_list(query_filters, page_number)

        self.assertFalse(response.ok)
        mock_post.assert_called_once()
        mock_capture_message.assert_called_once()

    def test_parse_datetime_valid(self):
        date_str_z = "2023-10-26T10:00:00+00:00"
        # datetime.fromisoformat correctly parses 'Z' as UTC since Python 3.7+
        # and makes the datetime object timezone-aware.
        expected_datetime_z = datetime(2023, 10, 26, 10, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(
            self.client_direct.parse_datetime(date_str_z), expected_datetime_z
        )

        date_str_offset = "2023-10-26T10:00:00+02:00"
        expected_datetime_offset = datetime(
            2023, 10, 26, 10, 0, 0, tzinfo=timezone(timedelta(hours=2))
        )
        self.assertEqual(
            self.client_direct.parse_datetime(date_str_offset), expected_datetime_offset
        )

    def test_parse_datetime_invalid(self):
        date_str = "invalid-date-string"
        self.assertIsNone(self.client_direct.parse_datetime(date_str))

    def test_parse_datetime_empty(self):
        date_str = ""
        self.assertIsNone(self.client_direct.parse_datetime(date_str))

    @patch("insights.sources.orders.clients.VtexOrdersRestClient.get_orders_list")
    def test_list_cache_hit(self, mock_get_orders_list):
        query_filters = {
            "utm_source": ["test_source"],
            "ended_at__gte": "2023-01-01T00:00:00Z",
            "ended_at__lte": "2023-01-31T23:59:59Z",
        }
        cache_key = self.client_direct.get_cache_key(query_filters)
        cached_data = {"countSell": 1, "accumulatedTotal": 100}
        self.mock_cache_client.get.return_value = json.dumps(cached_data)

        result = self.client_direct.list(query_filters)

        self.assertEqual(result, cached_data)
        self.mock_cache_client.get.assert_called_once_with(cache_key)
        mock_get_orders_list.assert_not_called()
        self.mock_cache_client.set.assert_not_called()

    def test_list_missing_utm_source(self):
        query_filters = {}
        expected_error = {"error": "utm_source field is mandatory"}
        self.mock_cache_client.get.return_value = (
            None  # Ensure no cache hit for this test
        )
        self.assertEqual(self.client_direct.list(query_filters), expected_error)

    @patch("insights.sources.orders.clients.as_completed")
    @patch("insights.sources.orders.clients.ThreadPoolExecutor")
    @patch("insights.sources.orders.clients.VtexOrdersRestClient.get_orders_list")
    def test_list_api_call_success_single_page(
        self, mock_get_orders_list, MockThreadPoolExecutor, mock_as_completed
    ):
        query_filters_initial = {
            "utm_source": ["wenivtex"],
            "ended_at__gte": "2023-01-01T00:00:00.000000+00:00",
            "ended_at__lte": "2023-01-01T01:00:00.000000+00:00",
        }
        query_filters_processed = {
            "utm_source": "wenivtex",
            "ended_at__gte": "2023-01-01T00:00:00.000000Z",
            "ended_at__lte": "2023-01-01T01:00:00.000000Z",
        }

        cache_key = self.client_direct.get_cache_key(query_filters_initial)
        self.mock_cache_client.get.return_value = None

        mock_api_response = MagicMock()
        mock_api_response.status_code = 200
        mock_api_response.json.return_value = {
            "list": [
                {
                    "status": "invoiced",
                    "totalValue": 15000,
                    "currencyCode": "BRL",
                },
                {
                    "status": "invoiced",
                    "totalValue": 25000,
                    "currencyCode": "BRL",
                },
                {"status": "canceled", "totalValue": 5000, "currencyCode": "BRL"},
            ],
            "paging": {"pages": 1, "currentPage": 1, "total": 3, "perPage": 100},
        }
        mock_get_orders_list.return_value = mock_api_response

        expected_result = {
            "countSell": 2,
            "accumulatedTotal": 400.00,
            "ticketMax": 250.00,
            "ticketMin": 150.00,
            "medium_ticket": 200.00,
            "currencyCode": "BRL",
        }

        mock_executor_instance = (
            MockThreadPoolExecutor.return_value.__enter__.return_value
        )

        # Ensure the lambda submitted to the executor is actually called
        def submit_calls_lambda_and_returns_future(func, *args_lambda, **kwargs_lambda):
            # func is: lambda page=page: self.get_orders_list(...)
            # This execution of func() is the second call to mock_get_orders_list.
            result_of_lambda = func()
            future = MagicMock(spec=Future)
            future.result.return_value = (
                result_of_lambda  # This will be mock_api_response again
            )
            return future

        mock_executor_instance.submit.side_effect = (
            submit_calls_lambda_and_returns_future
        )
        mock_as_completed.side_effect = lambda page_futures_dict: list(
            page_futures_dict.keys()
        )

        actual_result = self.client_direct.list(query_filters_initial.copy())

        self.assertEqual(actual_result, expected_result)
        self.mock_cache_client.get.assert_called_once_with(cache_key)

        # query_filters_processed is for the first call (paging)
        # expected_filters_for_api_call includes 'page': 1 for the executor call
        expected_filters_for_api_call = query_filters_processed.copy()
        expected_filters_for_api_call["page"] = 1

        self.assertEqual(mock_get_orders_list.call_count, 2)

        # Check first call (paging)
        paging_call_actual_args = mock_get_orders_list.call_args_list[0][0]
        self.assertEqual(paging_call_actual_args[0], query_filters_processed)
        self.assertEqual(paging_call_actual_args[1], 1)  # page number for paging call

        # Check second call (executor)
        executor_call_actual_args = mock_get_orders_list.call_args_list[1][0]
        self.assertEqual(executor_call_actual_args[0], expected_filters_for_api_call)
        self.assertEqual(
            executor_call_actual_args[1], 1
        )  # page number for executor call

        mock_executor_instance.submit.assert_called_once()

        self.mock_cache_client.set.assert_called_once_with(
            cache_key, json.dumps(expected_result), ex=3600
        )

    @patch("insights.sources.orders.clients.as_completed")
    @patch("insights.sources.orders.clients.ThreadPoolExecutor")
    @patch("insights.sources.orders.clients.VtexOrdersRestClient.get_orders_list")
    def test_list_api_error_no_list_in_data(
        self, mock_get_orders_list, MockThreadPoolExecutor, mock_as_completed
    ):
        query_filters = {
            "utm_source": ["test"],
            "ended_at__gte": "2023-01-01T00:00:00.000000+00:00",  # Consistent parsable format
        }
        self.mock_cache_client.get.return_value = None

        mock_api_response = MagicMock()
        mock_api_response.status_code = 200
        mock_api_response.json.return_value = {
            "error": "some vtex error",
            "paging": {"pages": 1},
        }
        mock_get_orders_list.return_value = mock_api_response

        # Mocks for executor and as_completed are included as per original test structure,
        # though they might not be strictly necessary if list() returns early.
        mock_executor_instance = (
            MockThreadPoolExecutor.return_value.__enter__.return_value
        )
        mock_future = MagicMock(spec=Future)
        mock_future.result.return_value = mock_api_response
        mock_executor_instance.submit.return_value = mock_future
        mock_as_completed.side_effect = lambda fs: [f for f in fs.keys()]

        status_code, data = self.client_direct.list(query_filters.copy())

        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"error": "some vtex error", "paging": {"pages": 1}})
        self.mock_cache_client.set.assert_not_called()

        processed_query_filters = {
            "utm_source": "test",
            "ended_at__gte": "2023-01-01T00:00:00.000000Z",  # Expected format after client processing
        }
        mock_get_orders_list.assert_called_once_with(processed_query_filters, 1)

    @patch("insights.sources.orders.clients.as_completed")
    @patch("insights.sources.orders.clients.ThreadPoolExecutor")
    @patch("insights.sources.orders.clients.requests.get")
    @patch("insights.sources.orders.clients.logger.error")
    def test_list_api_call_http_error(
        self,
        mock_logger_error,
        mock_requests_get,
        MockThreadPoolExecutor,
        mock_as_completed,
    ):
        query_filters = {
            "utm_source": ["test"],
            "ended_at__gte": "2023-01-01T00:00:00.000000+00:00",
        }
        self.mock_cache_client.get.return_value = None

        mock_initial_response = MagicMock()
        mock_initial_response.ok = True
        mock_initial_response.status_code = 200
        mock_initial_response.json.return_value = {
            "list": [],
            "paging": {"pages": 1, "currentPage": 1, "total": 0, "perPage": 100},
        }

        mock_error_response = MagicMock()
        mock_error_response.ok = False
        mock_error_response.status_code = 500
        mock_error_response.text = "Internal Server Error"

        mock_requests_get.side_effect = [mock_initial_response, mock_error_response]

        mock_executor_instance = (
            MockThreadPoolExecutor.return_value.__enter__.return_value
        )

        # Ensure the lambda submitted to the executor is actually called
        # so that get_orders_list (containing logger.error) is executed.
        def submit_calls_lambda(func, *args_lambda, **kwargs_lambda):
            # The func is: lambda page=page: self.get_orders_list({**query_filters, "page": page}, page,)
            # When this func() is called, it executes get_orders_list.
            # Inside that get_orders_list, requests.get is called (our mock_requests_get).
            # mock_requests_get returns mock_error_response (for the 2nd call).
            # Then get_orders_list calls logger.error and returns mock_error_response.
            result_of_lambda = func()  # This is critical

            # Create a future whose result is the result_of_lambda
            future = MagicMock(spec=Future)
            future.result.return_value = result_of_lambda
            return future

        mock_executor_instance.submit.side_effect = submit_calls_lambda

        # as_completed needs to yield the future created by our submit_calls_lambda
        # The client code builds: page_futures = { executor.submit(...): page ... }
        # So, as_completed will iterate over the keys of this dict.
        mock_as_completed.side_effect = lambda page_futures_dict: list(
            page_futures_dict.keys()
        )

        expected_result = {
            "countSell": 0,
            "accumulatedTotal": 0.0,
            "ticketMax": float("-inf"),
            "ticketMin": float("inf"),
            "medium_ticket": 0,
            "currencyCode": None,
        }

        actual_result = self.client_direct.list(query_filters.copy())

        self.assertEqual(actual_result, expected_result)
        mock_logger_error.assert_called_once()
        self.assertEqual(mock_requests_get.call_count, 2)

        # The cache key for set should be based on the initial query_filters passed to list()
        initial_query_filters_for_cache = {
            "utm_source": ["test"],
            "ended_at__gte": "2023-01-01T00:00:00.000000+00:00",
        }
        self.mock_cache_client.set.assert_called_once_with(
            self.client_direct.get_cache_key(initial_query_filters_for_cache),
            json.dumps(expected_result),
            ex=3600,
        )
