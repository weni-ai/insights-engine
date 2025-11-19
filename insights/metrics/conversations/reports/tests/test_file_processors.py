from django.test import TestCase

from insights.metrics.conversations.reports.dataclass import (
    ConversationsReportWorksheet,
)
from insights.metrics.conversations.reports.file_processors import (
    CSVFileProcessor,
    XLSXFileProcessor,
)
from insights.projects.models import Project
from insights.reports.choices import ReportFormat
from insights.reports.models import Report
from insights.users.models.user import User


class TestCSVFileProcessor(TestCase):
    def setUp(self):
        self.processor = CSVFileProcessor()
        self.project = Project.objects.create(name="Test")
        self.user = User.objects.create(email="test@test.com", language="en")
        self.source = "test_source"

    def test_process_csv_with_empty_worksheets(self):
        """Test CSV processing with empty worksheets."""
        worksheets = [
            ConversationsReportWorksheet(name="Empty", data=[]),
            ConversationsReportWorksheet(
                name="Valid", data=[{"col1": "val1", "col2": "val2"}]
            ),
        ]

        report = Report.objects.create(
            project=self.project,
            source=self.source,
            source_config={},
            filters={},
            format=ReportFormat.CSV,
            requested_by=self.user,
        )

        files = self.processor.process(report=report, worksheets=worksheets)

        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "Valid.csv")


class TestXLSXFileProcessor(TestCase):
    def setUp(self):
        self.processor = XLSXFileProcessor()
        self.project = Project.objects.create(name="Test")
        self.user = User.objects.create(email="test@test.com", language="en")
        self.source = "test_source"

    def test_process_xlsx_with_empty_worksheets(self):
        """Test XLSX processing with empty worksheets."""
        worksheets = [
            ConversationsReportWorksheet(name="Empty", data=[]),
            ConversationsReportWorksheet(
                name="Valid", data=[{"col1": "val1", "col2": "val2"}]
            ),
        ]

        report = Report.objects.create(
            project=self.project,
            source=self.source,
            source_config={},
            filters={},
            format=ReportFormat.XLSX,
            requested_by=self.user,
        )

        files = self.processor.process(report=report, worksheets=worksheets)

        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].name.endswith(".xlsx"))

    def test_ensure_unique_worksheet_name_with_truncation_needed(self):
        """Test worksheet name generation when truncation is needed for unique name."""
        used_names = set()
        long_name = "A" * 30  # Just under the limit

        # Add the original name to used_names
        used_names.add(long_name)

        result = self.processor._ensure_unique_worksheet_name(long_name, used_names)

        # Should be truncated to fit " (1)" suffix
        self.assertEqual(len(result), 31)
        self.assertTrue(result.endswith(" (1)"))

    def test_ensure_unique_worksheet_name_with_too_many_duplicates(self):
        """Test worksheet name generation when too many duplicates exist."""
        used_names = set()

        # Add the base name first
        used_names.add("Test")

        # Fill up to the limit (20) - need to add 20 more to trigger the limit
        for i in range(1, 21):
            used_names.add(f"Test ({i})")

        # The method should try to find a unique name and hit the limit
        with self.assertRaises(ValueError) as context:
            self.processor._ensure_unique_worksheet_name("Test", used_names)

        self.assertEqual(str(context.exception), "Too many unique names found")

    def test_process_xlsx_with_duplicate_worksheet_names(self):
        """Test XLSX processing with duplicate worksheet names."""
        worksheets = [
            ConversationsReportWorksheet(name="Test", data=[{"col1": "val1"}]),
            ConversationsReportWorksheet(name="Test", data=[{"col1": "val2"}]),
            ConversationsReportWorksheet(name="Test", data=[{"col1": "val3"}]),
        ]

        report = Report.objects.create(
            project=self.project,
            source=self.source,
            source_config={},
            filters={},
            format=ReportFormat.XLSX,
            requested_by=self.user,
        )

        files = self.processor.process(report=report, worksheets=worksheets)

        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].name.endswith(".xlsx"))

    def test_ensure_unique_worksheet_name_with_long_name(self):
        """Test worksheet name truncation when name exceeds max length."""
        used_names = set()
        long_name = "A" * 50  # Exceeds XLSX_WORKSHEET_NAME_MAX_LENGTH (31)

        result = self.processor._ensure_unique_worksheet_name(long_name, used_names)

        self.assertEqual(len(result), 31)
        self.assertTrue(result.startswith("A"))

    def test_ensure_unique_worksheet_name(self):
        used_names = set()
        self.assertEqual(
            self.processor._ensure_unique_worksheet_name("Test", used_names), "Test"
        )
        self.assertEqual(
            self.processor._ensure_unique_worksheet_name("Test", used_names), "Test (1)"
        )
        self.assertEqual(
            self.processor._ensure_unique_worksheet_name("Test", used_names), "Test (2)"
        )
        self.assertEqual(
            self.processor._ensure_unique_worksheet_name("Test (1)", used_names),
            "Test (1) (1)",
        )
