from abc import ABC, abstractmethod
import io
import csv
import logging
import os
import tempfile
from typing import Iterable

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
    ) -> list[ConversationsReportFile]:
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

            file_content_bytes = file_content.encode("utf-8")
            files.append(ConversationsReportFile(name=name, content=file_content_bytes))

        return files


class XLSXFileProcessor(FileProcessor):
    """
    Processor for xlsx files.
    """

    def process(
        self, report: Report, worksheets: list[ConversationsReportWorksheet]
    ) -> list[ConversationsReportFile]:
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


class StreamingXLSXFileProcessor:
    """
    XLSX processor that writes to a temp file on disk instead of keeping
    everything in memory. Accepts generators/iterables for worksheet data
    so rows can be written incrementally.
    """

    def __init__(self):
        self._used_worksheet_names: set[str] = set()

    def create_workbook(self, report: Report) -> tuple[xlsxwriter.Workbook, str]:
        """
        Create a workbook backed by a temp file. Returns (workbook, tmp_path).
        The caller must call finalize() when done.
        """
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".xlsx")
        os.close(tmp_fd)
        workbook = xlsxwriter.Workbook(tmp_path)
        return workbook, tmp_path

    def write_worksheet(
        self,
        workbook: xlsxwriter.Workbook,
        name: str,
        headers: list[str],
        rows: Iterable[dict],
    ) -> int:
        """
        Write a worksheet from an iterable of row dicts.
        Returns the number of data rows written.
        """
        worksheet_name = XLSXFileProcessor()._ensure_unique_worksheet_name(
            name, self._used_worksheet_names
        )
        xlsx_worksheet = workbook.add_worksheet(worksheet_name)
        xlsx_worksheet.write_row(0, 0, headers)

        row_count = 0
        for row_num, row_data in enumerate(rows, start=1):
            xlsx_worksheet.write_row(row_num, 0, [row_data.get(h, "") for h in headers])
            row_count += 1

        return row_count

    def finalize(
        self, workbook: xlsxwriter.Workbook, tmp_path: str, report: Report
    ) -> list[ConversationsReportFile]:
        """
        Close the workbook, read the file content, clean up, and return
        the report file.
        """
        workbook.close()

        with override(report.requested_by.language):
            file_name = gettext("Conversations dashboard report")

        try:
            with open(tmp_path, "rb") as f:
                content = f.read()
        finally:
            os.unlink(tmp_path)

        return [ConversationsReportFile(name=f"{file_name}.xlsx", content=content)]


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
