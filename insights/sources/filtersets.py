class GenericSQLFilter:
    """Responsible for cleaning and validating Filter data"""

    def __init__(
        self,
        source_field: str,
        table_alias: str,
        join_clause: dict = {},
        value: any = None,
    ) -> None:
        self.source_field = source_field
        self.table_alias = table_alias
        self.join_clause = join_clause
