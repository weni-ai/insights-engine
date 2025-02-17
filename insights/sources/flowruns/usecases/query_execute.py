from insights.db.elasticsearch.connection import Connection
from insights.sources.filter_strategies import ElasticSearchFilterStrategy
from insights.sources.flowruns.clients import (
    FlowRunElasticSearchQueryGenerator,
)
from insights.sources.flowruns.filtersets import FlowRunFilterSet
from insights.sources.flowruns.query_builder import (
    FlowRunElasticSearchQueryBuilder,
)


def transform_results_data(
    total: int, others: int, terms_agg_buckets: list[dict]
) -> list[dict]:
    transformed_results = []

    for term in terms_agg_buckets:
        full_value = term.get("doc_count")

        if full_value == 0 or full_value is None:
            transformed_results.append(
                {"label": term.get("key"), "value": 0, full_value: 0}
            )
            continue

        percentage = round(((full_value / total) * 100), 2)
        transformed_results.append(
            {"label": term.get("key"), "value": percentage, "full_value": full_value}
        )

    return transformed_results


class QueryExecutor:
    def execute(
        filters: dict,
        operation: str,
        parser: callable,
        query_kwargs: dict = {},
        *args,
        **kwargs,
    ) -> dict:
        query_generator = FlowRunElasticSearchQueryGenerator(
            filter_strategy=ElasticSearchFilterStrategy,
            query_builder=FlowRunElasticSearchQueryBuilder,
            filterset=FlowRunFilterSet,
            filters=filters,
            query_type=operation,
            query_kwargs=query_kwargs,
        )
        endpoint, params = query_generator.generate()
        response = Connection(endpoint).get(params=params)

        if operation == "recurrence":
            terms_agg = (
                response.get("aggregations", {}).get("values", {}).get("agg_field")
            )
            transformed_terms = transform_results_data(
                total=terms_agg.get("doc_count", 0),
                others=terms_agg.get("agg_value", {}).get("sum_other_doc_count", 0),
                terms_agg_buckets=terms_agg.get("agg_value", {}).get("buckets", []),
            )
            if len(transformed_terms) == 1:
                return transformed_terms[0]
            return {
                "results": transformed_terms,
            }
        elif operation == "count":
            print("executou aqui")
            print(operation)
            return {"value": response.get("count", 0)}
        else:
            return (
                response.get("aggregations", {})
                .get("values", {})
                .get("agg_field", {})
                .get("agg_value")
            )
