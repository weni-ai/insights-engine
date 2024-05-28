import pytest
from django.db.utils import IntegrityError

from insights.widgets.models import Report, Widget


@pytest.mark.django_db
def test_create_widget(create_default_dashboard):
    """
    separate report from widget
    create this inside a transaction atomic block
    """
    dash = create_default_dashboard

    widget = Widget.objects.create(
        dashboard=dash,
        name="Active Rooms",
        w_type="card",
        source="rooms",
        position={
            "example": "the logic behind the position config should be on the use case"
        },
        config={
            "example": "the logic behind the widget config should be on the use case"
        },
    )
    report = Report.objects.create(
        name="report", w_type="card", source="rooms", config={}, widget=widget
    )

    assert dash.widgets.count() == 1
    assert str(widget) == "Active Rooms"
    assert str(report) == "report"


@pytest.mark.parametrize(
    "remove_config",
    [
        "dashboard",
        "name",
        "w_type",
        "source",
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
