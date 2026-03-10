from django.test import TestCase
from django.core.exceptions import ValidationError

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

        with self.assertRaises(ValidationError) as context:
            Widget.objects.create(
                dashboard=self.dashboard,  # has dashboard
                parent=parent,  # has parent
                name="Test Widget",
                source="Test Source",
                position={},
                config={},
                type="test",
            )

        self.assertEqual(
            context.exception.messages[0],
            "Widget cannot have both parent and dashboard.",
        )

    def test_create_widget_without_parent_and_dashboard(self):
        with self.assertRaises(ValidationError) as context:
            Widget.objects.create(
                # does not have parent or dashboard
                name="Test Widget",
                source="Test Source",
                position={},
                config={},
                type="test",
            )

        self.assertEqual(
            context.exception.messages[0],
            "Widget cannot have both parent and dashboard.",
        )

    def test_change_a_widget_to_have_both_parent_and_dashboard(self):
        widget = Widget.objects.create(
            name="Test Widget",
            source="Test Source",
            dashboard=self.dashboard,
            position={},
            config={},
            type="test",
        )
        parent = Widget.objects.create(
            name="Parent Widget",
            dashboard=self.dashboard,
            source="Test Source",
            position={},
            config={},
            type="test",
        )
        widget.parent = parent
        widget.dashboard = self.dashboard

        with self.assertRaises(ValidationError) as context:
            widget.save()

        self.assertEqual(
            context.exception.messages[0],
            "Widget cannot have both parent and dashboard.",
        )

    def test_change_a_parent_widget_to_have_a_widget_as_child(self):
        parent = Widget.objects.create(
            name="Parent Widget",
            dashboard=self.dashboard,
            source="Test Source",
            position={},
            config={},
            type="test",
        )
        widget = Widget.objects.create(
            name="Test Widget",
            parent=parent,
            source="Test Source",
            position={},
            config={},
            type="test",
        )
        parent.children.add(widget)
        parent.save()
        self.assertEqual(parent.children.count(), 1)
        self.assertEqual(parent.children.first(), widget)

    def test_change_a_child_widget_to_have_a_child(self):
        parent = Widget.objects.create(
            name="Parent Widget",
            dashboard=self.dashboard,
            source="Test Source",
            position={},
            config={},
            type="test",
        )
        child = Widget.objects.create(
            name="Child Widget",
            parent=parent,
            source="Test Source",
            position={},
            config={},
            type="test",
        )
        grandchild = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="Test Source",
            position={},
            config={},
            type="test",
        )

        with self.assertRaises(ValidationError) as context:
            grandchild.parent = child
            grandchild.dashboard = None
            grandchild.save()

        self.assertEqual(
            context.exception.messages[0],
            "A widget that has a parent cannot have a grandparent.",
        )

    def test_change_a_widget_with_children_to_have_a_parent(self):
        widget_1 = Widget.objects.create(
            name="Widget 1",
            dashboard=self.dashboard,
            source="Test Source",
            position={},
            config={},
            type="test",
        )
        widget_2 = Widget.objects.create(
            name="Widget 2",
            dashboard=self.dashboard,
            source="Test Source",
            position={},
            config={},
            type="test",
        )
        Widget.objects.create(
            name="Widget 3",
            parent=widget_2,
            source="Test Source",
            position={},
            config={},
            type="test",
        )

        with self.assertRaises(ValidationError) as context:
            widget_2.dashboard = None
            widget_2.parent = widget_1
            widget_2.save()

        self.assertEqual(
            context.exception.messages[0],
            "A widget that is being added to a parent cannot have children.",
        )

    def test_change_a_widget_without_children_to_have_a_parent(self):
        widget_1 = Widget.objects.create(
            name="Widget 1",
            dashboard=self.dashboard,
            source="Test Source",
            position={},
            config={},
            type="test",
        )
        widget_2 = Widget.objects.create(
            name="Widget 2",
            dashboard=self.dashboard,
            source="Test Source",
            position={},
            config={},
            type="test",
        )
        widget_2.dashboard = None
        widget_2.parent = widget_1
        widget_2.save()
