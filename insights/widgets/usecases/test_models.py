import pytest

from insights.widgets.models import Widget, Report
from insights.dashboards.models import Dashboard
from insights.projects.models import Project


@pytest.mark.django_db
class TestWidget:
    @pytest.fixture
    def project(self):
        return Project.objects.create(name="Test Project")

    @pytest.fixture
    def dashboard(self, project):
        return Dashboard.objects.create(name="Test Dashboard", project=project)

    @pytest.fixture
    def widget(self, dashboard):
        return Widget.objects.create(
            name="Test Widget",
            type="type1",
            source="source1",
            config={"config_type": "crossing_data", "filter": {}},
            dashboard=dashboard,
            position={"x": 0, "y": 0},
        )

    @pytest.fixture
    def widget_2(self, dashboard):
        return Widget.objects.create(
            name="Test Widget",
            type="type1",
            source="source1",
            config={
                "filter": {"status": "active"},
                "live_filter": {"status": "live"},
            },
            dashboard=dashboard,
            position={"x": 0, "y": 0},
        )

    def test_widget_str(self, widget):
        assert str(widget) == "Test Widget"

    def test_widget_is_crossing_data(self, widget):
        assert widget.is_crossing_data is True

    def test_widget_project(self, widget):
        assert widget.project == widget.dashboard.project

    def test_widget_is_configurable(self, widget):
        assert widget.is_configurable is True

    def test_source_config(self, widget):
        filters, operation, op_field, op_sub_field, limit = widget.source_config()
        assert filters == {}
        assert operation == "list"
        assert op_field is None
        assert op_sub_field is None
        assert limit is None

    def test_source_config_live(self, widget_2):
        filters, operation, op_field, op_sub_field, limit = widget_2.source_config(
            is_live=True
        )
        assert filters == {
            "status": "live",
        }  # live_filter sobrescreve o filter existente
        assert operation == "list"
        assert op_field is None
        assert op_sub_field is None
        assert limit is None


@pytest.mark.django_db
class TestReport:
    @pytest.fixture
    def project(self):
        return Project.objects.create(name="Test Project")

    @pytest.fixture
    def dashboard(self, project):
        return Dashboard.objects.create(name="Test Dashboard", project=project)

    @pytest.fixture
    def widget(self, dashboard):
        return Widget.objects.create(
            name="Test Widget",
            type="type1",
            source="source1",
            config={"config_type": "crossing_data", "filter": {}},
            dashboard=dashboard,
            position={"x": 0, "y": 0},
        )

    @pytest.fixture
    def report(self, widget):
        return Report.objects.create(
            name="Test Report",
            type="report_type",
            source="report_source",
            config={"config_type": "crossing_data", "filter": {}},
            widget=widget,
        )

    def test_report_str(self, report):
        assert str(report) == "Test Report"

    def test_report_project(self, report):
        assert report.project == report.widget.project

    def test_report_source_config(self, report):
        filters, operation, op_field, op_sub_field, limit = report.source_config()
        assert filters == {}
        assert operation == "list"
        assert op_field is None
        assert op_sub_field is None
        assert limit is None
