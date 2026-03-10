from django.test import TestCase
from django.db.utils import IntegrityError

from insights.widgets.models import Widget
from insights.projects.models import Project
from insights.dashboards.models import Dashboard


class TestWidget(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.dashboard = Dashboard.objects.create(
            project=self.project,
            name="Test Dashboard",
        )

    def test_create_widget_with_dashboard(self):
        widget = Widget.objects.create(
            dashboard=self.dashboard,
            name="Test Widget",
            position={},
            type="test",
            source="Test Source",
            config={},
        )
        self.assertEqual(widget.dashboard, self.dashboard)

    def test_create_widget_with_parent(self):
        parent = Widget.objects.create(
            dashboard=self.dashboard,  # has dashboard
            name="Parent Widget",
            source="Test Source",
            position={},
            config={},
            type="test",
        )
        widget = Widget.objects.create(
            # does not have dashboard
            parent=parent,
            name="Test Widget",
            source="Test Source",
            position={},
            config={},
            type="test",
        )
        self.assertEqual(widget.parent, parent)

    def test_create_widget_with_dashboard_and_parent(self):
        parent = Widget.objects.create(
            name="Parent Widget",
            dashboard=self.dashboard,  # has dashboard
            source="Test Source",
            position={},
            config={},
            type="test",
        )

        with self.assertRaises(IntegrityError) as context:
            Widget.objects.create(
                dashboard=self.dashboard,  # has dashboard
                parent=parent,  # has parent
                name="Test Widget",
                source="Test Source",
                position={},
                config={},
                type="test",
            )

        self.assertTrue(
            str(context.exception).startswith(
                'new row for relation "widgets_widget" violates check constraint "widget_parent_xor_dashboard"'
            )
        )

    def test_create_widget_without_parent_and_dashboard(self):
        with self.assertRaises(IntegrityError) as context:
            Widget.objects.create(
                # does not have parent or dashboard
                name="Test Widget",
                source="Test Source",
                position={},
                config={},
                type="test",
            )

        self.assertTrue(
            str(context.exception).startswith(
                'new row for relation "widgets_widget" violates check constraint "widget_parent_xor_dashboard"'
            )
        )
