import requests
from insights.internals.base import VtexAuthentication
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from insights.sources.vtexcredentials.clients import AuthRestClient
from insights.sources.cache import CacheClient
from insights.utils import format_to_iso_utc
from django.conf import settings


class VtexOrdersRestClient(VtexAuthentication):
    def __init__(self, auth_params, cache_client: CacheClient) -> None:
        self.headers = {
            "X-VTEX-API-AppToken": settings.MOCK_APPTOKEN,
            "X-VTEX-API-AppKey": settings.MOCK_APPKEY,
        }
        self.base_url = settings.MOCKDOMAIN
        self.cache = cache_client

    def get_cache_key(self, query_filters):
        """Gere uma chave única para o cache baseada nos filtros de consulta."""
        return f"vtex_data:{json.dumps(query_filters, sort_keys=True)}"

    def get_vtex_endpoint(self, query_filters: dict, page_number: int = 1):
        start_date = query_filters.get("start_date")
        end_date = query_filters.get("end_date")
        utm_source = query_filters.get("utm_source")

        if start_date is not None:
            url = f"{self.base_url}/api/oms/pvt/orders/?f_UtmSource={utm_source}&per_page=100&page={page_number}&f_authorizedDate=authorizedDate:[{start_date} TO {end_date}]&f_status=invoiced"
        else:
            url = f"{self.base_url}/api/oms/pvt/orders/?f_UtmSource={utm_source}&per_page=100&page={page_number}&f_status=invoiced"
        return url

    def list(self, query_filters: dict):
        # cache_key = self.get_cache_key(query_filters)

        # cached_data = self.cache.get(cache_key)
        # if cached_data:
        #     return 200, json.loads(cached_data)

        if not query_filters.get("utm_source", None):
            return {"error": "utm_source field is mandatory"}

        if query_filters.get("created_on__gte", None):
            query_filters["start_date"] = format_to_iso_utc(
                query_filters.pop("created_on__gte")
            )

        if query_filters.get("created_on__lte", None):
            query_filters["end_date"] = format_to_iso_utc(
                query_filters.pop("created_on__lte"), end_of_day=True
            )

        if query_filters.get("utm_source", None):
            query_filters["utm_source"] = query_filters.pop("utm_source")

        total_value = 0
        total_sell = 0
        max_value = float("-inf")
        min_value = float("inf")

        response = requests.get(
            self.get_vtex_endpoint(query_filters), headers=self.headers
        )
        data = response.json()

        if "list" not in data or not data["list"]:
            return response.status_code, data

        pages = data["paging"]["pages"] if "paging" in data else 1

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
        }

        # self.cache.set(cache_key, json.dumps(result_data), ex=3600)

        return response.status_code, result_data
