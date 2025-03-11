from urllib.parse import urlencode
import requests
from insights.internals.base import VtexAuthentication
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from insights.sources.vtexcredentials.clients import AuthRestClient
from insights.sources.cache import CacheClient
from insights.utils import format_to_iso_utc
from django.conf import settings

from datetime import datetime


class VtexOrdersRestClient(VtexAuthentication):
    def __init__(
        self,
        auth_params: dict,
        cache_client: CacheClient,
        use_io_proxy: bool = False,
    ) -> None:
        self.use_io_proxy = use_io_proxy
        self.headers = {}

        if not use_io_proxy:
            self.headers = {
                "X-VTEX-API-AppToken": auth_params.get("app_token"),
                "X-VTEX-API-AppKey": auth_params.get("app_key"),
            }

        self.base_url = auth_params.get("domain")

        if "https://" not in self.base_url:
            self.base_url = f"https://{self.base_url}"

        if "myvtex.com" not in self.base_url:
            self.base_url = f"{self.base_url}.myvtex.com"

        self.cache = cache_client

    def get_cache_key(self, query_filters):
        """Gere uma chave única para o cache baseada nos filtros de consulta."""
        return f"vtex_data:{json.dumps(query_filters, sort_keys=True)}"

    def get_vtex_endpoint(self, query_filters: dict, page_number: int = 1):
        start_date = query_filters.get("ended_at__gte")
        end_date = query_filters.get("ended_at__lte")
        utm_source = query_filters.get("utm_source")

        # When the app is integrated with VTEX IO, we use the IO as a proxy to get the orders list
        # instead of making requests directly to the VTEX API
        path = "/_v/orders/" if self.use_io_proxy else "/api/oms/pvt/orders/"

        query_params = {
            "f_UtmSource": utm_source,
            "per_page": 100,
            "page": page_number,
            "f_status": "invoiced",
        }

        if start_date is not None:
            query_params["f_authorizedDate"] = (
                f"authorizedDate:[{start_date} TO {end_date}]"
            )

        url = f"{self.base_url}{path}?{urlencode(query_params)}"

        return url

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

        response = requests.get(
            self.get_vtex_endpoint(query_filters), headers=self.headers
        )
        data = response.json()

        if "list" not in data:
            return response.status_code, data

        pages = data["paging"]["pages"] if "paging" in data else 1

        currency_code = None

        # botar o max_workers em variavel de ambiente
        with ThreadPoolExecutor(max_workers=10) as executor:
            page_futures = {
                executor.submit(
                    lambda page=page: requests.get(
                        self.get_vtex_endpoint({**query_filters, "page": page}),
                        headers=self.headers,
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
                        print(
                            f"Request failed with status code: {response.status_code}"
                        )
                except Exception as exc:
                    print(f"Generated an exception: {exc}")

        total_value /= 100
        max_value /= 100
        min_value /= 100
        medium_ticket = total_value / total_sell if total_sell > 0 else 0

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
