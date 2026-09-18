from insights.sources.channels.enums import Channel


def test_channel_values():
    assert Channel.INSTAGRAM == "instagram"
    assert Channel.FACEBOOK == "facebook"
    assert Channel.WHATSAPP == "whatsapp"
    assert Channel.TEAMS == "teams"
    assert Channel.EMAIL == "email"
    assert Channel.SHOPPING_ASSISTANT == "shopping_assistant"
    assert Channel.OTHERS == "others"


def test_urn_case_sql_maps_known_schemes_and_falls_back_to_others():
    sql = Channel.urn_case_sql()
    assert "instagram:%" in sql
    assert "whatsapp:%" in sql
    assert "ext:%" in sql
    assert "mailto:%" in sql
    assert f"THEN '{Channel.SHOPPING_ASSISTANT}'" in sql
    assert f"THEN '{Channel.EMAIL}'" in sql
    assert f"ELSE '{Channel.OTHERS}'" in sql
    assert "SPLIT_PART" not in sql


def test_valid_values_keeps_only_enum_members():
    assert Channel.valid_values(["whatsapp", "nope", "email"]) == [
        "whatsapp",
        "email",
    ]
    assert Channel.valid_values("facebook") == ["facebook"]
    assert Channel.valid_values(None) == []


def test_urn_prefix_filter_sql_known_channels():
    sql, params = Channel.urn_prefix_filter_sql("r.urn", ["whatsapp", "instagram"])
    assert sql == "(r.urn LIKE (%s) OR r.urn LIKE (%s))"
    assert params == ["whatsapp:%", "instagram:%"]


def test_urn_prefix_filter_sql_teams_and_shopping_assistant():
    sql, params = Channel.urn_prefix_filter_sql(
        "r.urn", ["teams", "shopping_assistant"]
    )
    assert sql == (
        "(r.urn LIKE (%s) OR r.urn LIKE (%s) OR r.urn LIKE (%s) OR r.urn LIKE (%s))"
    )
    assert params == ["teams:%", "msteams:%", "ext:%", "shopping_assistant:%"]


def test_urn_prefix_filter_sql_others_with_known_channel():
    sql, params = Channel.urn_prefix_filter_sql("r.urn", ["whatsapp", "others"])
    assert sql.startswith("(r.urn LIKE (%s) OR (NOT (")
    assert "OR r.urn IS NULL)" in sql
    assert params[0] == "whatsapp:%"
    assert "instagram:%" in params
    assert params.count("whatsapp:%") == 2
