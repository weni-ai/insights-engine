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
