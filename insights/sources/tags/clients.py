from insights.sources.clients import GenericSQLQueryGenerator


class TagSQLQueryGenerator(GenericSQLQueryGenerator):
    default_query_type = "list"
