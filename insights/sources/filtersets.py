class GenericSQLFilter:
    """Responsible for cleaning and validating Filter data"""

    def __init__(
        self,
        source_field: str,
        table_alias: str,
        join_clause: dict = {},
        value: any = None,
        default_operation: str = None,
    ) -> None:
        self.source_field = source_field
        self.table_alias = table_alias
        self.join_clause = join_clause
        self.default_operation = default_operation


class GenericElasticSearchFilter:
    """Responsible for cleaning and validating Filter data"""

    def __init__(
        self,
        source_field: str,
        field_type: str,
    ) -> None:
        self.source_field = source_field
        self.field_type = field_type
