class BasicFilterStrategy:
    def apply(self, field, operation, value, table_alias):
        if operation == "after" or operation == "gte":
            return f"{table_alias}.{field} >= (%s)", [value]
        elif operation == "before" or operation == "lte":
            return f"{table_alias}.{field} <= (%s)", [value]
        elif operation == "eq":
            return f"{table_alias}.{field} = (%s)", [value]
        elif operation == "in":
            placeholders = ", ".join(["%s"] * len(value))
            return f"{table_alias}.{field} IN ({placeholders})", list(value)
        elif operation == "icontains":
            return f"{table_alias}.{field} ILIKE (%s)", [f"%{value}%"]
        elif operation == "isnull":
            placeholder = "IS NOT NULL" if value is True else "IS NULL"
            return f"{table_alias}.{field} {placeholder}", None
        elif operation == "or":
            if type(field) is not dict:
                raise ValueError(
                    "On 'or' operations, the field needs to be a dict sub_field_name: sub_table_alias"
                )
            or_clauses = []
            or_params = []
            for sub_field_name, sub_table_alias in field.items():
                sub_clause, sub_params = self.apply(
                    sub_field_name, "icontains", value, sub_table_alias
                )
                or_clauses.append(sub_clause)
                or_params.extend(sub_params)
            return f"({' OR '.join(or_clauses)})", or_params
        else:
            raise ValueError(f"Unsupported operation: {operation}")
