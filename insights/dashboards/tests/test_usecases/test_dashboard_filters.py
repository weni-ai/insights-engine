import pytest

from insights.dashboards.models import Dashboard
from insights.dashboards.usecases.dashboard_filters import get_dash_filters


@pytest.mark.django_db
def test_get_dash_filters_atendimento_humano():
    dash = Dashboard(name="Atendimento humano")

    filters = get_dash_filters(dash)

    assert "contact" in filters
    assert filters["contact"]["type"] == "input_text"
    assert filters["contact"]["label"] == "filter.contact.label"

    assert "created_on" in filters
    assert filters["created_on"]["type"] == "date_range"
    assert filters["created_on"]["label"] == "filter.created_on.label"

    assert "sector" in filters
    assert filters["sector"]["type"] == "select"
    assert filters["sector"]["field"] == "uuid"

    assert "queue" in filters
    assert filters["queue"]["type"] == "select"
    assert filters["queue"]["depends_on"] == {
        "filter": "sector",
        "search_param": "sector_id",
    }

    assert "agent" in filters
    assert filters["agent"]["type"] == "select"
    assert filters["agent"]["field"] == "email"

    assert "tags" in filters
    assert filters["tags"]["type"] == "select"
    assert filters["tags"]["depends_on"] == {
        "filter": "sector",
        "search_param": "sector_id",
    }


@pytest.mark.django_db
def test_get_dash_filters_outro_dashboard():
    dash = Dashboard(name="Outro nome")

    filters = get_dash_filters(dash)

    assert "ended_at" in filters
    assert filters["ended_at"]["type"] == "date_range"
    assert filters["ended_at"]["label"] is None
