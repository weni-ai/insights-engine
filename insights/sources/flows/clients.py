from insights.sources.clients import GenericSQLQueryGenerator


class FlowSQLQueryGenerator(GenericSQLQueryGenerator):
    default_query_type = "list"
