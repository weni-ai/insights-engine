from django.db.models import TextChoices


class Channel(TextChoices):
    INSTAGRAM = "instagram", "Instagram"
    FACEBOOK = "facebook", "Facebook"
    WHATSAPP = "whatsapp", "WhatsApp"
    TEAMS = "teams", "Teams"
    EMAIL = "email", "Email"
    SHOPPING_ASSISTANT = "shopping_assistant", "Shopping assistant"
    OTHERS = "others", "Others"

    @classmethod
    def valid_values(cls, values) -> list[str]:
        if values is None:
            return []
        if not isinstance(values, list):
            values = [values]
        allowed = set(cls.values)
        return [value for value in values if value in allowed]

    @classmethod
    def urn_prefixes_by_channel(cls) -> dict[str, tuple[str, ...]]:
        return {
            cls.INSTAGRAM: ("instagram:",),
            cls.FACEBOOK: ("facebook:",),
            cls.WHATSAPP: ("whatsapp:",),
            cls.TEAMS: ("teams:", "msteams:"),
            cls.EMAIL: ("email:", "mailto:"),
            cls.SHOPPING_ASSISTANT: ("ext:", "shopping_assistant:"),
        }

    @classmethod
    def known_urn_prefixes(cls) -> tuple[str, ...]:
        prefixes: list[str] = []
        for channel_prefixes in cls.urn_prefixes_by_channel().values():
            prefixes.extend(channel_prefixes)
        return tuple(prefixes)

    @classmethod
    def urn_case_sql(cls, column: str = "r.urn") -> str:
        when_clauses = []
        for channel, prefixes in cls.urn_prefixes_by_channel().items():
            for prefix in prefixes:
                when_clauses.append(
                    f"WHEN {column} LIKE '{prefix}%%' THEN '{channel}'"
                )
        when_sql = "\n                ".join(when_clauses)
        return f"""
            CASE
                {when_sql}
                ELSE '{cls.OTHERS}'
            END
        """

    @classmethod
    def urn_prefix_filter_sql(
        cls, column: str, values
    ) -> tuple[str, list[str] | None]:
        channels = cls.valid_values(values)
        if not channels:
            return "FALSE", None

        include_others = cls.OTHERS in channels
        clauses: list[str] = []
        params: list[str] = []

        for channel in channels:
            if channel == cls.OTHERS:
                continue
            for prefix in cls.urn_prefixes_by_channel()[channel]:
                clauses.append(f"{column} LIKE (%s)")
                params.append(f"{prefix}%")

        if include_others:
            others_likes = [f"{column} LIKE (%s)" for _ in cls.known_urn_prefixes()]
            # CASE ELSE treats NULL urn as others; NOT LIKE alone would drop those rows
            clauses.append(
                f"(NOT ({' OR '.join(others_likes)}) OR {column} IS NULL)"
            )
            params.extend(f"{prefix}%" for prefix in cls.known_urn_prefixes())

        if len(clauses) == 1:
            return clauses[0], params
        return f"({' OR '.join(clauses)})", params
