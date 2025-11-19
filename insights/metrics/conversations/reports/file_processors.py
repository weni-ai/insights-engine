from abc import ABC, abstractmethod
import io
import csv
import logging
import xlsxwriter

from django.utils.translation import gettext, override
from insights.metrics.conversations.reports.dataclass import (
    ConversationsReportFile,
    ConversationsReportWorksheet,
)
from insights.reports.choices import ReportFormat
from insights.reports.models import Report


logger = logging.getLogger(__name__)


CSV_FILE_NAME_MAX_LENGTH = 31
XLSX_FILE_NAME_MAX_LENGTH = 31
XLSX_WORKSHEET_NAME_MAX_LENGTH = 31


class FileProcessor(ABC):
    """
    Base class for file processors.
    """

    @abstractmethod
    def process(
        self, report: Report, worksheets: list[ConversationsReportWorksheet]
    ) -> ConversationsReportFile:
        raise NotImplementedError("Subclasses must implement this method")


class CSVFileProcessor(FileProcessor):
    """
    Processor for csv files.
    """

    def process(
        self, report: Report, worksheets: list[ConversationsReportWorksheet]
    ) -> ConversationsReportFile:
        """
        Process the csv for the conversations report.
        """
        files: list[ConversationsReportFile] = []

        for worksheet in worksheets:
            if len(worksheet.data) == 0:
                logger.info(
                    "[CONVERSATIONS REPORT SERVICE] Worksheet %s has no data",
                    worksheet.name,
                )
                continue

            with io.StringIO() as csv_buffer:
                fieldnames = list(worksheet.data[0].keys()) if worksheet.data else []
                writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(worksheet.data)
                file_content = csv_buffer.getvalue()

            name = worksheet.name[: CSV_FILE_NAME_MAX_LENGTH - 4] + ".csv"

            files.append(ConversationsReportFile(name=name, content=file_content))

        return files


class XLSXFileProcessor(FileProcessor):
    """
    Processor for xlsx files.
    """

    def process(
        self, report: Report, worksheets: list[ConversationsReportWorksheet]
    ) -> ConversationsReportFile:
        """
        Process the xlsx for the conversations report.
        """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})

        with override(report.requested_by.language):
            file_name = gettext("Conversations dashboard report")

        used_worksheet_names = set()
        for worksheet in worksheets:
            if len(worksheet.data) == 0:
                logger.info(
                    "[CONVERSATIONS REPORT SERVICE] Worksheet %s has no data",
                    worksheet.name,
                )
                continue

            worksheet_name = self._ensure_unique_worksheet_name(
                worksheet.name, used_worksheet_names
            )
            worksheet_data = worksheet.data

            xlsx_worksheet = workbook.add_worksheet(worksheet_name)
            xlsx_worksheet.write_row(0, 0, worksheet_data[0].keys())

            for row_num, row_data in enumerate(worksheet_data, start=1):
                xlsx_worksheet.write_row(row_num, 0, row_data.values())

        workbook.close()
        output.seek(0)

        return [
            ConversationsReportFile(name=f"{file_name}.xlsx", content=output.getvalue())
        ]

    def _ensure_unique_worksheet_name(self, name: str, used_names: set[str]) -> str:
        """
        Ensure worksheet name is unique by appending a number if needed.

        Args:
            name: The original worksheet name
            used_names: Set of already used worksheet names

        Returns:
            A unique worksheet name
        """

        name = name[:XLSX_WORKSHEET_NAME_MAX_LENGTH]

        if name not in used_names:
            used_names.add(name)
            return name

        counter = 1
        while f"{name} ({counter})" in used_names:
            counter += 1

            if counter > 20:
                raise ValueError("Too many unique names found")

        unique_name = f"{name} ({counter})"

        if len(unique_name) > XLSX_WORKSHEET_NAME_MAX_LENGTH:
            counter_length = len(f" ({counter})")
            new_name = name[: XLSX_WORKSHEET_NAME_MAX_LENGTH - counter_length]
            unique_name = f"{new_name} ({counter})"

        used_names.add(unique_name)
        return unique_name


FILE_PROCESSORS = {
    ReportFormat.CSV: CSVFileProcessor,
    ReportFormat.XLSX: XLSXFileProcessor,
}


def get_file_processor(format: ReportFormat) -> FileProcessor:
    """
    Get the file processor for the given format.
    """
    if format not in FILE_PROCESSORS:
        raise ValueError(f"Invalid format: {format}")

    return FILE_PROCESSORS[format]()
