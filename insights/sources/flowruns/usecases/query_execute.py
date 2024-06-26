from insights.db.elasticsearch.connection import Connection
from insights.sources.flowruns.clients import FlowRunsElasticSearchClient


def transform_terms_count_to_percentage(
    total: int, others: int, terms_agg_buckets: list[dict]
) -> list[dict]:
    transformed_results = []
    for term in terms_agg_buckets:
        value = term.get("doc_count")
        if value == 0:
            transformed_results.append({"value": term.get("key"), "percentage": "0%"})
            continue
        percent = (value / total) * 100
        transformed_results.append(
            {"value": term.get("key"), "percentage": f"{percent}%"}
        )
    return transformed_results


class QueryExecutor:
    def execute(
        filters: dict,
        operation: str,
        parser: callable,
        project: object,
        query_kwargs: dict = {},
        *args,
        **kwargs,
    ) -> dict:
        filters["project"] = str(project.uuid)
        client = FlowRunsElasticSearchClient()
        endpoint, params = client.execute(
            filters=filters, query_type=operation, query_kwargs=query_kwargs
        )
        response = Connection(endpoint).get(params=params)

        if operation == "recurrence":
            terms_agg = (
                response.get("aggregations", {}).get("values", {}).get("agg_field")
            )
            transformed_terms = transform_terms_count_to_percentage(
                total=terms_agg.get("doc_count", 0),
                others=terms_agg.get("agg_value", {}).get("sum_other_doc_count", 0),
                terms_agg_buckets=terms_agg.get("agg_value", {}).get("buckets", []),
            )
            return {
                "results": transformed_terms,
            }
        elif operation == "count":
            return {"value": response.get("count", 0)}
        else:
            return (
                response.get("aggregations", {})
                .get("values", {})
                .get("agg_field", {})
                .get("agg_value")
            )
