from urllib.parse import urlparse, parse_qs, urlencode

from rest_framework.request import Request

from insights.core.urls.dataclass import PaginationURLs


def get_cursor_based_pagination_urls(
    request: Request,
    response_body: dict,
    page_size_param: str = "page_size",
    cursor_param: str = "cursor",
) -> PaginationURLs:
    """
    Get the pagination cursor params from the request.
    """
    insights_uri = request.build_absolute_uri()
    insights_url = urlparse(insights_uri)
    insights_endpoint = f"https://{insights_url.netloc}{insights_url.path}"
    query_params = parse_qs(insights_url.query)
    page_size = query_params.get(page_size_param, [None])[0]
    query_params.pop(cursor_param, None)

    response_next = response_body.get("next")
    response_previous = response_body.get("previous")

    next_url = None
    previous_url = None

    if response_next:
        response_next_parsed = urlparse(response_next)
        response_next_query_params = parse_qs(response_next_parsed.query)
        next_cursor = response_next_query_params.get(cursor_param, [None])[0]

        next_query_params = query_params.copy()

        if next_cursor:
            next_query_params[cursor_param] = next_cursor
        if page_size:
            next_query_params[page_size_param] = page_size

        next_url = f"{insights_endpoint}?{urlencode(next_query_params)}"

    if response_previous:
        response_previous_parsed = urlparse(response_previous)
        previous_query_params = parse_qs(response_previous_parsed.query)
        previous_cursor = previous_query_params.get(cursor_param, [None])[0]

        previous_full_query_params = {**query_params, **previous_query_params}
        previous_url = f"{insights_endpoint}?{urlencode(previous_full_query_params)}"

        if previous_cursor:
            previous_query_params[cursor_param] = previous_cursor
        if page_size:
            previous_query_params[page_size_param] = page_size

    return PaginationURLs(
        next_url=next_url,
        previous_url=previous_url,
    )
