from insights.sources.clients import GenericSQLQueryGenerator


class SectorSQLQueryGenerator(GenericSQLQueryGenerator):
    default_query_type = "list"
