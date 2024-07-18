from insights.sources.clients import GenericElasticSearchQueryGenerator

flow_runs_filters = {
    "created_on": {"type": "date", "to_field": "created_on"},
    "exited_on": {"type": "date", "to_field": "exited_on"},
    "ended_at": {"type": "date", "to_field": "exited_on"},
    "project": {"type": "string", "to_field": "project_uuid"},
    "flow": {"type": "string", "to_field": "flow_uuid"},
}


class FlowRunElasticSearchQueryGenerator(GenericElasticSearchQueryGenerator):
    default_query_type = "count"
