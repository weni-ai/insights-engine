from unittest.mock import patch

from django.test import TestCase

from insights.dashboards.tasks import check_and_create_ctwa_dashboard
from insights.projects.models import Project


class TestCheckAndCreateCTWADashboardTask(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")

    @patch(
        "insights.dashboards.tasks.CheckAndCreateCTWADashboardUseCase"
    )
    def test_task_delegates_to_usecase(self, mock_usecase_cls):
        mock_usecase = mock_usecase_cls.return_value

        check_and_create_ctwa_dashboard(str(self.project.uuid))

        mock_usecase_cls.assert_called_once_with()
        mock_usecase.execute.assert_called_once_with(str(self.project.uuid))
