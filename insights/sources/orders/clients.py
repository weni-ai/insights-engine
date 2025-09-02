import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import urlencode


import requests
from sentry_sdk import capture_message

from insights.internals.base import VtexAuthentication
from insights.sources.cache import CacheClient
from insights.utils import redact_headers

logger = logging.getLogger(__name__)


class VtexOrdersRestClient(VtexAuthentication):
    def __init__(
        self,
        auth_params: dict,
        cache_client: CacheClient,
        use_io_proxy: bool = False,
    ) -> None:
        self.use_io_proxy = use_io_proxy
        self.headers = {}
        self.internal_token = None

        self.base_url = auth_params.get("domain")

        if self.use_io_proxy:
            if "https://" not in self.base_url:
                self.base_url = f"https://{self.base_url}"

            if "myvtex.com" not in self.base_url:
                self.base_url = f"{self.base_url}.myvtex.com"

            self.headers = {
                "X-Weni-Auth": auth_params.get("internal_token"),
            }
        else:
            self.headers = {
                "X-VTEX-API-AppToken": auth_params.get("app_token"),
                "X-VTEX-API-AppKey": auth_params.get("app_key"),
            }

        self.cache = cache_client

    def get_cache_key(self, query_filters):
        """Gere uma chave única para o cache baseada nos filtros de consulta."""
        return f"vtex_data:{json.dumps(query_filters, sort_keys=True)}"

    def get_query_params(self, query_filters: dict, page_number: int):
        start_date = query_filters.get("ended_at__gte")
        end_date = query_filters.get("ended_at__lte")
        utm_source = query_filters.get("utm_source")

        query_params = {
            "f_UtmSource": utm_source,
            "per_page": 100,
            "page": page_number,
            "f_status": "invoiced",
        }

        if start_date:
            query_params["f_authorizedDate"] = (
                f"authorizedDate:[{start_date} TO {end_date}]"
            )

        return query_params

    def get_vtex_endpoint(
        self,
        query_filters: dict,
        page_number: int = 1,
    ):
        if self.use_io_proxy:
            # Using IO as a proxy to get the orders list
            # because, when the app is integrated with VTEX IO, we can't make requests directly to the VTEX API
            # as we don't have the app key and app token
            path = "/_v/orders/"
            return f"{self.base_url}{path}"

        path = "/api/oms/pvt/orders/"
        query_params = self.get_query_params(query_filters, page_number)
        return f"{self.base_url}{path}?{urlencode(query_params)}"

    def get_request_body(self, query_filters: dict, page_number: int):
        """
        This method is used to get the request body for the VTEX IO proxy.
        """
        if self.use_io_proxy:
            query_params = self.get_query_params(query_filters, page_number)
            return {
                "raw_query": query_params,
            }
        else:
            return {}

    def get_orders_list(self, query_filters: dict, page_number: int, timeout=60):
        """
        This method is used to get the orders list from the VTEX API.
        """
        endpoint = self.get_vtex_endpoint(query_filters, page_number)

        request_details = {
            "url": endpoint,
            "headers": redact_headers(
                self.headers,
                ["X-VTEX-API-AppToken", "X-VTEX-API-AppKey", "X-Weni-Auth"],
            ),
        }

        if self.use_io_proxy:
            body = self.get_request_body(query_filters, page_number)
            request_details["method"] = "POST"
            request_details["json"] = body

            response = requests.post(
                endpoint,
                headers=self.headers,
                json=body,
                timeout=timeout,
            )
        else:
            request_details["method"] = "GET"
            response = requests.get(endpoint, headers=self.headers, timeout=timeout)

        if not response.ok:
            capture_message(
                f"Error fetching orders. URL: {endpoint}. Status code: {response.status_code}. Response: {response.text}",
                level="error",
            )

            response_details = {
                "status_code": response.status_code,
                "text": response.text,
                "url": response.url,
                "headers": response.headers,
            }

            logger.error(
                "[VTEX Orders] Response (%s): Error on request URL: %s"
                % (response_details["status_code"], response_details["url"]),
                stack_info=False,
                extra={
                    "response_details": response_details,
                    "request_details": request_details,
                },
            )

        return response

    def parse_datetime(self, date_str):
        try:
            # Tente fazer o parse da string para datetime
            return datetime.fromisoformat(date_str)  # Para strings ISO formatadas
        except ValueError:
            return None  # Retorne None se a conversão falhar

    def list(self, query_filters: dict):
        cache_key = self.get_cache_key(query_filters)

        cached_data = self.cache.get(cache_key)
        if cached_data:
            return json.loads(cached_data)

        if not query_filters.get("utm_source", None):
            return {"error": "utm_source field is mandatory"}

        if query_filters.get("ended_at__gte", None):
            start_date_str = query_filters["ended_at__gte"]
            start_date = self.parse_datetime(start_date_str)
            if start_date:
                query_filters["ended_at__gte"] = start_date.strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                )

        if query_filters.get("ended_at__lte", None):
            end_date_str = query_filters["ended_at__lte"]
            end_date = self.parse_datetime(end_date_str)
            if end_date:
                query_filters["ended_at__lte"] = end_date.strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                )

        if query_filters.get("utm_source", None):
            query_filters["utm_source"] = query_filters.pop("utm_source")[0]

        total_value = 0
        total_sell = 0
        max_value = float("-inf")
        min_value = float("inf")

        response = self.get_orders_list(query_filters, 1)
        data = response.json()

        if "list" not in data:
            return response.status_code, data

        pages = data["paging"]["pages"] if "paging" in data else 1

        currency_code = None

        # botar o max_workers em variavel de ambiente
        with ThreadPoolExecutor(max_workers=10) as executor:
            page_futures = {
                executor.submit(
                    lambda page=page: self.get_orders_list(
                        {**query_filters, "page": page},
                        page,
                    )
                ): page
                for page in range(1, pages + 1)
            }

            for page_future in as_completed(page_futures):
                try:
                    response = page_future.result()
                    if response.status_code == 200:
                        results = response.json()
                        for result in results["list"]:
                            if result["status"] != "canceled":
                                total_value += result["totalValue"]
                                total_sell += 1
                                max_value = max(max_value, result["totalValue"])
                                min_value = min(min_value, result["totalValue"])

                                if currency_code is None:
                                    currency_code = result["currencyCode"]
                    else:
                        logger.error(
                            f"VTEX API error processing page: status={response.status_code}, response={response.text}"
                        )
                except Exception as exc:
                    logger.error(f"VTEX API error processing page: {exc}")
                    # Continue processing other pages instead of just printing

        total_value = total_value / 100
        max_value = (max_value / 100) if max_value != float("-inf") else 0
        min_value = (min_value / 100) if min_value != float("inf") else 0
        medium_ticket = (total_value / total_sell) if total_sell > 0 else 0

        result_data = {
            "countSell": total_sell,
            "accumulatedTotal": total_value,
            "ticketMax": max_value,
            "ticketMin": min_value,
            "medium_ticket": medium_ticket,
            "currencyCode": currency_code,
        }

        self.cache.set(cache_key, json.dumps(result_data), ex=3600)

        return result_data
