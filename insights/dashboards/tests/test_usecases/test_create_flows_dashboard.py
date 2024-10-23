import pytest
from unittest.mock import patch, MagicMock
from insights.dashboards.models import Dashboard
from insights.widgets.models import Widget
from insights.dashboards.usecases.flows_dashboard_creation import CreateFlowsDashboard
from insights.dashboards.usecases.exceptions import InvalidDashboardObject
from insights.projects.usecases.dashboard_dto import FlowsDashboardCreationDTO


@pytest.fixture
def flows_dashboard_params():
    return FlowsDashboardCreationDTO(
        project=MagicMock(),
        dashboard_name="Test Dashboard",
        funnel_amount=3,
        currency_type="USD",
    )


@patch("insights.dashboards.models.Dashboard.objects.create")
@pytest.mark.django_db
def test_create_dashboard_exception(mock_dashboard_create, flows_dashboard_params):
    mock_dashboard_create.side_effect = Exception("Database Error")

    create_dashboard = CreateFlowsDashboard(flows_dashboard_params)

    with pytest.raises(
        InvalidDashboardObject, match="Error creating dashboard: Database Error"
    ):
        create_dashboard.create_dashboard()


@patch("insights.widgets.models.Widget.objects.create")
@pytest.mark.django_db
def test_create_graph_funnel_widgets(mock_widget_create, flows_dashboard_params):
    create_dashboard = CreateFlowsDashboard(flows_dashboard_params)
    mock_dashboard = MagicMock()

    create_dashboard.create_graph_funnel_widgets(mock_dashboard, 3)

    assert mock_widget_create.call_count == 3
    mock_widget_create.assert_any_call(
        name="",
        type="empty_column",
        source="",
        config={},
        dashboard=mock_dashboard,
        position={"rows": [1, 3], "columns": [1, 4]},
    )


@patch("insights.widgets.models.Widget.objects.create")
@pytest.mark.django_db
def test_create_card_widgets(mock_widget_create, flows_dashboard_params):
    create_dashboard = CreateFlowsDashboard(flows_dashboard_params)
    mock_dashboard = MagicMock()

    create_dashboard.create_card_widgets(mock_dashboard, 3)

    assert mock_widget_create.call_count == 3
    mock_widget_create.assert_any_call(
        name="",
        type="card",
        source="",
        config={},
        dashboard=mock_dashboard,
        position={"rows": [1, 1], "columns": [1, 4]},
    )


@patch("insights.widgets.models.Widget.objects.create")
@pytest.mark.django_db
def test_create_default_card_widgets(mock_widget_create, flows_dashboard_params):
    create_dashboard = CreateFlowsDashboard(flows_dashboard_params)
    mock_dashboard = MagicMock()

    create_dashboard.create_default_card_widgets(mock_dashboard)

    assert mock_widget_create.call_count == 9
    mock_widget_create.assert_any_call(
        name="",
        type="card",
        source="",
        config={},
        dashboard=mock_dashboard,
        position={"rows": [1, 1], "columns": [1, 4]},
    )
