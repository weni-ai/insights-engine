from insights.sources.filters import ElasticSearchFilterStrategy
from insights.sources.flowruns.query_builder import (
    FlowRunsElasticSearchQueryBuilder,
)

flow_runs_filters = {
    "created_on": {"type": "date", "to_field": "created_on"},
    "exited_on": {"type": "date", "to_field": "exited_on"},
    "project": {"type": "string", "to_field": "project_uuid"},
    "flow": {"type": "string", "to_field": "flow_uuid"},
}


class FlowRunsElasticSearchClient:
    def execute(
        self,
        filters: dict,
        query_type: str = "count",
        query_kwargs: dict = {},
    ):
        strategy = ElasticSearchFilterStrategy()
        builder = FlowRunsElasticSearchQueryBuilder()

        for key, value in filters.items():
            if "__" in key:
                field, operation = key.split("__", 1)
            elif type(value) is list:
                field = key.split("__", 1)[0]
                operation = "in"
            else:
                field, operation = key, "eq"

            if (
                field in flow_runs_filters
            ):  # only consider filters describred in the flow_runs_filters dict. TODO: maybe transform this dict into a class similar to django-filters filterset classes
                field = flow_runs_filters[field]["to_field"]
            else:
                continue
            builder.add_filter(strategy, field, operation, value)
        builder.build_query()

        return getattr(builder, query_type)(**query_kwargs)
