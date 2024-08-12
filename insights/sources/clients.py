class GenericSQLQueryGenerator:
    default_query_type = "count"

    def __init__(
        self,
        filter_strategy,
        query_builder,
        filterset,
        filters: dict,
        query_type: str = "",
        query_kwargs: dict = {},
    ) -> None:
        self.filter_strategy = filter_strategy
        self.query_builder = query_builder
        self.filterset = filterset
        self.filters = filters
        self.query_type = query_type or self.default_query_type
        self.query_kwargs = query_kwargs

    def generate(self):
        strategy = self.filter_strategy()
        builder = self.query_builder()
        filterset = self.filterset()

        for key, value in self.filters.items():
            if "__" in key:
                field, operation = key.split("__", 1)
            elif type(value) is list:
                field = key.split("__", 1)[0]
                operation = "in"
            else:
                field, operation = key, "eq"
            field_object = filterset.get_field(field)
            if field_object is None:
                continue
            source_field = field_object.source_field
            join_clause = field_object.join_clause
            if join_clause != {}:
                builder.add_joins(join_clause)
            builder.add_filter(
                strategy, source_field, operation, value, field_object.table_alias
            )
        builder.build_query()

        return getattr(builder, self.query_type)(**self.query_kwargs)


class GenericElasticSearchQueryGenerator:
    default_query_type = "count"

    def __init__(
        self,
        filter_strategy,
        query_builder,
        filterset,
        filters: dict,
        query_type: str = "",
        query_kwargs: dict = {},
    ) -> None:
        self.filter_strategy = filter_strategy
        self.query_builder = query_builder
        self.filterset = filterset
        self.filters = filters
        self.query_type = query_type or self.default_query_type
        self.query_kwargs = query_kwargs

    def generate(self):
        # nessa função ocorre o erro
        strategy = self.filter_strategy()
        builder = self.query_builder()
        filterset = self.filterset()

        for key, value in self.filters.items():
            if "__" in key:
                field, operation = key.split("__", 1)
            elif type(value) is list:
                field = key.split("__", 1)[0]
                operation = "in"
            else:
                field, operation = key, "eq"
            field_object = filterset.get_field(field)
            if field_object is None:
                continue
            source_field = field_object.source_field
            builder.add_filter(strategy, source_field, operation, value)
        builder.build_query()
        print("query type", self.query_type)
        return getattr(builder, self.query_type)(**self.query_kwargs)
