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
    query_params_raw = parse_qs(insights_url.query)
    # Normalize query params: parse_qs returns lists, convert to single values
    query_params = {k: v[0] if v else None for k, v in query_params_raw.items()}
    page_size = query_params.get(page_size_param)
    query_params.pop(cursor_param, None)

    response_next = response_body.get("next")
    response_previous = response_body.get("previous")

    next_url = None
    previous_url = None

    if response_next:
        response_next_parsed = urlparse(response_next)
        response_next_query_params_raw = parse_qs(response_next_parsed.query)
        next_cursor = response_next_query_params_raw.get(cursor_param, [None])[0]

        next_query_params = query_params.copy()

        if next_cursor:
            next_query_params[cursor_param] = next_cursor
        if page_size:
            next_query_params[page_size_param] = page_size

        next_url = f"{insights_endpoint}?{urlencode(next_query_params)}"

    if response_previous:
        response_previous_parsed = urlparse(response_previous)
        previous_query_params_raw = parse_qs(response_previous_parsed.query)
        previous_cursor = previous_query_params_raw.get(cursor_param, [None])[0]

        previous_query_params = query_params.copy()

        if previous_cursor:
            previous_query_params[cursor_param] = previous_cursor
        if page_size:
            previous_query_params[page_size_param] = page_size

        previous_url = f"{insights_endpoint}?{urlencode(previous_query_params)}"

    return PaginationURLs(
        next_url=next_url,
        previous_url=previous_url,
    )


def get_limit_offset_pagination_urls(
    request: Request,
    response_body: dict,
    limit_param: str = "limit",
    offset_param: str = "offset",
) -> PaginationURLs:
    """
    Rewrite upstream limit/offset pagination URLs to point back through the proxy.
    """
    insights_uri = request.build_absolute_uri()
    insights_url = urlparse(insights_uri)
    insights_endpoint = f"https://{insights_url.netloc}{insights_url.path}"
    query_params_raw = parse_qs(insights_url.query)
    query_params = {k: v[0] if v else None for k, v in query_params_raw.items()}
    query_params.pop(limit_param, None)
    query_params.pop(offset_param, None)

    response_next = response_body.get("next")
    response_previous = response_body.get("previous")

    next_url = None
    previous_url = None

    if response_next:
        next_parsed = urlparse(response_next)
        next_qs = parse_qs(next_parsed.query)
        next_limit = next_qs.get(limit_param, [None])[0]
        next_offset = next_qs.get(offset_param, [None])[0]

        next_query_params = query_params.copy()
        if next_limit:
            next_query_params[limit_param] = next_limit
        if next_offset:
            next_query_params[offset_param] = next_offset

        next_url = f"{insights_endpoint}?{urlencode(next_query_params)}"

    if response_previous:
        prev_parsed = urlparse(response_previous)
        prev_qs = parse_qs(prev_parsed.query)
        prev_limit = prev_qs.get(limit_param, [None])[0]
        prev_offset = prev_qs.get(offset_param, [None])[0]

        previous_query_params = query_params.copy()
        if prev_limit:
            previous_query_params[limit_param] = prev_limit
        if prev_offset:
            previous_query_params[offset_param] = prev_offset

        previous_url = f"{insights_endpoint}?{urlencode(previous_query_params)}"

    return PaginationURLs(
        next_url=next_url,
        previous_url=previous_url,
    )
