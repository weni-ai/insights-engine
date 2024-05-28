import pytest

from insights.widgets.models import Report, Widget
from insights.widgets.usecases.create_by_template import (
    WidgetCreationDTO,
    WidgetCreationUseCase,
)
from insights.widgets.usecases.exceptions import InvalidWidgetObject


@pytest.mark.django_db
def test_create_widgets_in_dashboard(create_default_dashboard):
    dashboard = create_default_dashboard

    widget_list = [
        WidgetCreationDTO(
            dashboard=dashboard,
            name="widget magico",
            w_type="card",
            source="chats",
            position={"y": (0, 1), "x": (0, 1)},
            config={
                "description": "Mensagens trocadas via bot",
                "flow_uuid": "2c209ca9-f9d4-4f20-82c8-4e1acbae6c90",
                "type_result": 2,
                "operation": "count",
            },
            report={},
        )
    ]
    widget_use_case = WidgetCreationUseCase()
    widget_use_case.create_widgets(widget_dtos=widget_list)
    widget_inside_dashboard = Widget.objects.get(dashboard=dashboard)

    assert widget_inside_dashboard.dashboard.name == "Human Resources"


@pytest.mark.django_db
def test_create_widgets_empty_list():
    with pytest.raises(ValueError) as exc_info:
        widget_use_case = WidgetCreationUseCase()
        widget_use_case.create_widgets([])
    assert str(exc_info.value) == "widget list cannot be empty!"


@pytest.mark.django_db
def test_create_widgets_with_report(create_default_dashboard):
    dashboard = create_default_dashboard

    widget_list = [
        WidgetCreationDTO(
            dashboard=dashboard,
            name="widget magico",
            w_type="card",
            source="chats",
            position={"y": (0, 1), "x": (0, 1)},
            config={
                "description": "Mensagens trocadas via bot",
                "flow_uuid": "2c209ca9-f9d4-4f20-82c8-4e1acbae6c90",
                "type_result": 2,
                "operation": "count",
            },
            report={
                "name": "report magico",
                "w_type": "card",
                "source": "chats",
                "config": "{}",
            },
        )
    ]
    widget_use_case = WidgetCreationUseCase()
    widget_use_case.create_widgets(widget_dtos=widget_list)
    widget_inside_dashboard = Widget.objects.get(dashboard=dashboard)
    report_created = Report.objects.get(widget=widget_inside_dashboard)

    assert widget_inside_dashboard.dashboard.name == "Human Resources"
    assert report_created.widget == widget_inside_dashboard
    assert report_created.name == "report magico"


@pytest.mark.django_db
def test_create_widgets_without_fields():
    widget_list = [
        WidgetCreationDTO(
            dashboard=9999,
            name="widget magico",
            w_type="card",
            source="chats",
            position={"y": (0, 1), "x": (0, 1)},
            config={
                "description": "Mensagens trocadas via bot",
                "flow_uuid": "2c209ca9-f9d4-4f20-82c8-4e1acbae6c90",
                "type_result": 2,
                "operation": "count",
            },
            report={
                "name": "widget magico",
                "w_type": "card",
                "source": "chats",
                "config": "{}",
            },
        )
    ]

    widget_use_case = WidgetCreationUseCase()
    with pytest.raises(InvalidWidgetObject):
        widget_use_case.create_widgets(widget_dtos=widget_list)
