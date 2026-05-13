from rest_framework.test import APITestCase

from insights.authentication.authentication import User
from insights.projects.models import Project
from insights.reports.choices import ReportFormat, ReportSource, ReportStatus
from insights.reports.models import Report
from insights.reports.usecases.report_status_cache import ReportStatusCacheUseCase


class TestReportStatusCacheInvalidation(APITestCase):
    def setUp(self):
        self.user = User.objects.create(email="test@test.com")
        self.project = Project.objects.create(name="Test Project")
        self.project_uuid = str(self.project.uuid)

    def tearDown(self):
        ReportStatusCacheUseCase.invalidate(self.project_uuid)

    def test_cache_invalidated_on_report_create(self):
        ReportStatusCacheUseCase.set(self.project_uuid, None)

        Report.objects.create(
            project=self.project,
            source=ReportSource.CONVERSATIONS_DASHBOARD,
            format=ReportFormat.CSV,
            status=ReportStatus.PENDING,
            requested_by=self.user,
        )

        _, cache_hit = ReportStatusCacheUseCase.get(self.project_uuid)
        self.assertFalse(cache_hit)

    def test_cache_invalidated_on_status_change(self):
        report = Report.objects.create(
            project=self.project,
            source=ReportSource.CONVERSATIONS_DASHBOARD,
            format=ReportFormat.CSV,
            status=ReportStatus.PENDING,
            requested_by=self.user,
        )

        ReportStatusCacheUseCase.set(self.project_uuid, report)

        report.status = ReportStatus.IN_PROGRESS
        report.save()

        _, cache_hit = ReportStatusCacheUseCase.get(self.project_uuid)
        self.assertFalse(cache_hit)

    def test_cache_not_affected_for_different_project(self):
        other_project = Project.objects.create(name="Other Project")

        ReportStatusCacheUseCase.set(self.project_uuid, None)

        Report.objects.create(
            project=other_project,
            source=ReportSource.CONVERSATIONS_DASHBOARD,
            format=ReportFormat.CSV,
            status=ReportStatus.PENDING,
            requested_by=self.user,
        )

        _, cache_hit = ReportStatusCacheUseCase.get(self.project_uuid)
        self.assertTrue(cache_hit)
