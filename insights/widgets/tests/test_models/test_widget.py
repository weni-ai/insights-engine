import pytest
from django.db.utils import IntegrityError

from insights.widgets.models import Widget


@pytest.mark.django_db
def test_create_widget(create_default_dashboard):
    """
    separate report from widget
    create this inside a transaction atomic block
    """
    dash = create_default_dashboard

    Widget.objects.create(
        dashboard=dash,
        name="Active Rooms",
        w_type="card",
        source="rooms",
        report={
            "example": "the logic behind the report config should be on the use case"
        },
        position={
            "example": "the logic behind the position config should be on the use case"
        },
        config={
            "example": "the logic behind the widget config should be on the use case"
        },
    )
    assert dash.widgets.count() == 1


@pytest.mark.parametrize(
    "remove_config",
    [
        "dashboard",
        "name",
        "w_type",
        "source",
        "report",
        "position",
        "config",
    ],
)
@pytest.mark.django_db
def test_required_fields(remove_config: str, create_default_dashboard):
    dash = create_default_dashboard
    widget_config = {
        "dashboard": dash,
        "name": "Active Rooms",
        "w_type": "card",
        "source": "rooms",
        "report": {
            "example": "the logic behind the report config should be on the use case"
        },
        "position": {
            "example": "the logic behind the position config should be on the use case"
        },
        "config": {
            "example": "the logic behind the widget config should be on the use case"
        },
    }
    widget_config.pop(remove_config)
    with pytest.raises(IntegrityError):
        Widget.objects.create(**widget_config)
