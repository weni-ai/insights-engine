from insights.sources.clients import GenericSQLQueryGenerator


class QueueSQLQueryGenerator(GenericSQLQueryGenerator):
    default_query_type = "list"
