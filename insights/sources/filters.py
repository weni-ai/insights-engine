class BasicFilterStrategy:
    def apply(self, field, operation, value, table_alias):
        if operation == "after":
            return f"{table_alias}.{field} > (%s)", [value]
        elif operation == "before":
            return f"{table_alias}.{field} < (%s)", [value]
        elif operation == "eq":
            return f"{table_alias}.{field} = (%s)", [value]
        elif operation == "in":
            placeholders = ", ".join(["%s"] * len(value))
            return f"{table_alias}.{field} IN ({placeholders})", list(value)
        else:
            raise ValueError(f"Unsupported operation: {operation}")
