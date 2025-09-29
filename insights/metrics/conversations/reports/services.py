from datetime import datetime
import io
import csv
import xlsxwriter
import logging
from abc import ABC, abstractmethod
from datetime import datetime
import pytz

from django.core.mail import EmailMessage
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext, override
from django.utils import translation, timezone
from sentry_sdk import capture_exception

from insights.metrics.conversations.reports.dataclass import (
    ConversationsReportFile,
    ConversationsReportWorksheet,
)
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.reports.models import Report
from insights.reports.choices import ReportStatus, ReportFormat, ReportSource
from insights.users.models import User
from insights.projects.models import Project
from insights.sources.dl_events.clients import BaseDataLakeEventsClient
from insights.metrics.conversations.integrations.elasticsearch.services import (
    ConversationsElasticsearchService,
)


logger = logging.getLogger(__name__)


def serialize_filters_for_json(filters: dict) -> dict:
    """
    Serialize datetime objects in filters dictionary to JSON-compatible format.
    This ensures that filters containing datetime objects can be stored in JSONField.
    """
    if not filters:
        return filters

    serialized_filters = {}
    for key, value in filters.items():
        if isinstance(value, datetime):
            # Convert datetime to ISO format string
            serialized_filters[key] = value.isoformat()
        elif isinstance(value, dict):
            # Recursively handle nested dictionaries
            serialized_filters[key] = serialize_filters_for_json(value)
        elif isinstance(value, list):
            # Handle lists that might contain datetime objects
            serialized_list = []
            for item in value:
                if isinstance(item, datetime):
                    serialized_list.append(item.isoformat())
                elif isinstance(item, dict):
                    serialized_list.append(serialize_filters_for_json(item))
                else:
                    serialized_list.append(item)
            serialized_filters[key] = serialized_list
        else:
            serialized_filters[key] = value

    return serialized_filters


class BaseConversationsReportService(ABC):
    """
    Base class for conversations report services.
    """

    @abstractmethod
    def process_csv(
        self, report: Report, worksheets: list[ConversationsReportWorksheet]
    ) -> list[ConversationsReportFile]:
        """
        Process the csv for the conversations report.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def process_xlsx(
        self, report: Report, worksheets: list[ConversationsReportWorksheet]
    ) -> list[ConversationsReportFile]:
        """
        Process the xlsx for the conversations report.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def send_email(self, report: Report, file_content: str) -> None:
        """
        Send the email for the conversations report.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def request_generation(
        self,
        project: Project,
        source_config: dict,
        filters: dict,
        report_format: ReportFormat,
        requested_by: User,
    ) -> None:
        """
        Request the generation of a conversations report.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def generate(self, report: Report) -> None:
        """
        Start the generation of a conversations report.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def get_current_report_for_project(self, project: Project) -> bool:
        """
        Check if the project can receive new reports generation.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def get_next_report_to_generate(self) -> Report | None:
        """
        Get the next report to generate.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def get_datalake_events(self, report: Report, **kwargs) -> list[dict]:
        """
        Get datalake events.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def get_resolutions_worksheet(
        self,
        report: Report,
        start_date: datetime,
        end_date: datetime,
    ) -> ConversationsReportWorksheet:
        """
        Get the resolutions worksheet.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def get_flowsrun_results_by_contacts(
        self,
        report: Report,
        flow_uuid: str,
        start_date: str,
        end_date: str,
        op_field: str,
    ) -> list[dict]:
        """
        Get flowsrun results by contacts.
        """
        raise NotImplementedError("Subclasses must implement this method")


class ConversationsReportService(BaseConversationsReportService):
    """
    Service to generate conversations reports.
    """

    def __init__(
        self,
        datalake_events_client: BaseDataLakeEventsClient,
        metrics_service: ConversationsMetricsService,
        elasticsearch_service: ConversationsElasticsearchService,
        events_limit_per_page: int = 5000,
        page_limit: int = 100,
        elastic_page_size: int = 1000,
        elastic_page_limit: int = 100,
    ):
        self.source = ReportSource.CONVERSATIONS_DASHBOARD
        self.datalake_events_client = datalake_events_client
        self.metrics_service = metrics_service
        self.events_limit_per_page = events_limit_per_page
        self.page_limit = page_limit
        self.elasticsearch_service = elasticsearch_service
        self.elastic_page_size = elastic_page_size
        self.elastic_page_limit = elastic_page_limit

    def process_csv(
        self, report: Report, worksheets: list[ConversationsReportWorksheet]
    ) -> list[ConversationsReportFile]:
        """
        Process the csv for the conversations report.
        """
        files: list[ConversationsReportFile] = []

        for worksheet in worksheets:
            with io.StringIO() as csv_buffer:
                fieldnames = list(worksheet.data[0].keys()) if worksheet.data else []
                writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(worksheet.data)
                file_content = csv_buffer.getvalue()

            files.append(
                ConversationsReportFile(
                    name=f"{worksheet.name}.csv", content=file_content
                )
            )

        return files

    def _ensure_unique_worksheet_name(self, name: str, used_names: set[str]) -> str:
        """
        Ensure worksheet name is unique by appending a number if needed.

        Args:
            name: The original worksheet name
            used_names: Set of already used worksheet names

        Returns:
            A unique worksheet name
        """
        if name not in used_names:
            used_names.add(name)
            return name

        counter = 1
        while f"{name} ({counter})" in used_names:
            counter += 1

            if counter > 20:
                raise ValueError("Too many unique names found")

        unique_name = f"{name} ({counter})"
        used_names.add(unique_name)
        return unique_name

    def process_xlsx(
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

    def send_email(self, report: Report, files: list[ConversationsReportFile]) -> None:
        """
        Send the email for the conversations report.
        """
        # TODO: Send multiple files if report type is CSV
        with translation.override(report.requested_by.language):
            subject = _("Conversations dashboard report")
            body = _("Please find the conversations report attached.")

            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[report.requested_by.email],
            )

            for file in files:
                email.attach(
                    file.name,
                    file.content,
                    (
                        "application/csv"
                        if report.format == ReportFormat.CSV
                        else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    ),
                )

            email.send(fail_silently=False)

    def request_generation(
        self,
        project: Project,
        source_config: dict,
        filters: dict,
        report_format: ReportFormat,
        requested_by: User,
    ) -> None:
        """
        Request the generation of a conversations report.
        """
        logger.info(
            "[CONVERSATIONS REPORT SERVICE] Requesting generation of conversations report for project %s",
            project.uuid,
        )

        if not source_config:
            logger.error(
                "[CONVERSATIONS REPORT SERVICE] source_config is empty for project %s",
                project.uuid,
            )
            raise ValueError(
                "source_config cannot be empty when requesting generation of conversations report"
            )

        if not filters:
            logger.error(
                "[CONVERSATIONS REPORT SERVICE] filters is empty for project %s",
                project.uuid,
            )
            raise ValueError(
                "filters cannot be empty when requesting generation of conversations report"
            )

        sections = source_config.get("sections", [])
        custom_widgets = source_config.get("custom_widgets", [])

        if len(sections) == 0 and len(custom_widgets) == 0:
            logger.error(
                "[CONVERSATIONS REPORT SERVICE] sections or custom_widgets is empty for project %s",
                project.uuid,
            )
            raise ValueError(
                "sections or custom_widgets cannot be empty when requesting generation of conversations report"
            )

        # Serialize datetime objects in filters to make them JSON-compatible
        serialized_filters = serialize_filters_for_json(filters)

        report = Report.objects.create(
            project=project,
            source=self.source,
            source_config=source_config,
            filters=serialized_filters,
            format=report_format,
            requested_by=requested_by,
            status=ReportStatus.PENDING,
        )

        logger.info(
            "[CONVERSATIONS REPORT SERVICE] Conversations report created %s",
            report.uuid,
        )

        return report

    def generate(self, report: Report) -> None:
        """
        Start the generation of a conversations report.
        """
        logger.info(
            "[CONVERSATIONS REPORT SERVICE] Starting generation of conversations report %s",
            report.uuid,
        )
        report.status = ReportStatus.IN_PROGRESS
        report.started_at = timezone.now()
        report.save(update_fields=["status", "started_at"])

        try:
            filters = report.filters or {}

            start_date = filters.get("start")
            end_date = filters.get("end")

            if not start_date or not end_date:
                logger.error(
                    "[CONVERSATIONS REPORT SERVICE] Start date or end date is missing for report %s",
                    report.uuid,
                )
                raise ValueError(
                    "Start date or end date is missing for report %s" % report.uuid
                )

            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)

            logger.info(
                "[CONVERSATIONS REPORT SERVICE] Start date: %s, End date: %s",
                start_date,
                end_date,
            )

            sections = report.source_config.get("sections", [])

            worksheets = []

            if "RESOLUTIONS" in sections:
                resolutions_worksheet = self.get_resolutions_worksheet(
                    report,
                    report.filters.get("start"),
                    report.filters.get("end"),
                )
                worksheets.append(resolutions_worksheet)

            files: list[ConversationsReportFile] = []

            if report.format == ReportFormat.CSV:
                files.extend(self.process_csv(report, worksheets))
            elif report.format == ReportFormat.XLSX:
                files.extend(self.process_xlsx(report, worksheets))

        except Exception as e:
            logger.error(
                "[CONVERSATIONS REPORT SERVICE] Failed to generate report %s. Error: %s",
                report.uuid,
                e,
            )
            report.status = ReportStatus.FAILED
            report.completed_at = timezone.now()
            errors = report.errors or {}
            errors["generate"] = str(e)
            errors["event_id"] = capture_exception(e)
            report.errors = errors
            report.save(update_fields=["status", "completed_at", "errors"])
            raise e

        logger.info(
            "[CONVERSATIONS REPORT SERVICE] Sending email for conversations report %s to %s",
            report.uuid,
            report.requested_by.email,
        )

        try:
            self.send_email(report, files)
        except Exception as e:
            event_id = capture_exception(e)
            logger.error(
                "[CONVERSATIONS REPORT SERVICE] Failed to send email for conversations report %s. Event_id: %s",
                report.uuid,
                event_id,
            )
            report.status = ReportStatus.FAILED
            report.completed_at = timezone.now()
            errors = report.errors or {}
            errors["send_email"] = str(e)
            errors["event_id"] = event_id
            report.errors = errors
            report.save(update_fields=["status", "completed_at", "errors"])
            raise e

        logger.info(
            "[CONVERSATIONS REPORT SERVICE] Email for conversations report %s sent to %s",
            report.uuid,
            report.requested_by.email,
        )

        report.status = ReportStatus.READY
        report.completed_at = timezone.now()
        report.save(update_fields=["status", "completed_at"])

        logger.info(
            "[CONVERSATIONS REPORT SERVICE] Conversations report completed %s",
            report.uuid,
        )

    def get_current_report_for_project(self, project: Project) -> Report | None:
        """
        Check if the project can receive new reports generation.
        """
        return (
            Report.objects.filter(
                project=project,
                source=self.source,
                status__in=[ReportStatus.PENDING, ReportStatus.IN_PROGRESS],
            )
            .order_by("created_on")
            .first()
        )

    def get_next_report_to_generate(self) -> Report | None:
        """
        Get the next report to generate.
        """
        return (
            Report.objects.filter(
                source=self.source,
                status=ReportStatus.PENDING,
            )
            .order_by("created_on")
            .first()
        )

    def get_datalake_events(self, report: Report, **kwargs) -> list[dict]:
        """
        Get datalake events.
        """
        limit = self.events_limit_per_page
        offset = 0

        events = []

        current_page = 1
        page_limit = self.page_limit

        while True:
            if current_page >= page_limit:
                logger.error(
                    "[CONVERSATIONS REPORT SERVICE] Report %s has more than %s pages. Finishing datalake events retrieval"
                    % (
                        report.uuid,
                        page_limit,
                    ),
                )
                raise ValueError("Report has more than %s pages" % page_limit)

            report.refresh_from_db(fields=["status"])

            if report.status != ReportStatus.IN_PROGRESS:
                logger.info(
                    "[CONVERSATIONS REPORT SERVICE] Report %s is not in progress. Finishing datalake events retrieval",
                    report.uuid,
                )
                raise ValueError("Report %s is not in progress" % report.uuid)

            logger.info(
                "[CONVERSATIONS REPORT SERVICE] Retrieving datalake events for page %s for report %s",
                current_page,
                report.uuid,
            )

            paginated_events = self.datalake_events_client.get_events(
                **kwargs,
                limit=limit,
                offset=offset,
            )

            if len(paginated_events) == 0 or paginated_events == [{}]:
                break

            events.extend(paginated_events)
            offset += limit
            current_page += 1

        return events

    def _format_date(self, date_str: str, report: Report) -> str:
        """
        Format the date.
        """
        formats = ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S"]

        datetime_date = None

        for _format in formats:
            try:
                datetime_date = datetime.strptime(date_str, _format)
                break
            except Exception as e:
                logger.error(
                    "[CONVERSATIONS REPORT SERVICE] Failed to format date %s for report %s. Error: %s"
                    % (
                        date_str,
                        report.uuid,
                        e,
                    ),
                )
                capture_exception(e)
                continue

        if not datetime_date:
            try:
                datetime_date = datetime.fromisoformat(date_str)
            except Exception as e:
                logger.error(
                    "[CONVERSATIONS REPORT SERVICE] Failed to format date %s for report %s. Error: %s"
                    % (
                        date_str,
                        report.uuid,
                        e,
                    ),
                )
                capture_exception(e)
                raise e

        tz_name = report.project.timezone

        if tz_name:
            tz = pytz.timezone(tz_name)
            datetime_date = datetime_date.astimezone(tz)

        return datetime_date.strftime("%d/%m/%Y %H:%M:%S")

    def get_flowsrun_results_by_contacts(
        self,
        report: Report,
        flow_uuid: str,
        start_date: str,
        end_date: str,
        op_field: str,
    ) -> list[dict]:
        """
        Get flowsrun results by contacts.
        """
        data = []

        current_page = 1
        page_size = self.elastic_page_size
        page_limit = self.elastic_page_limit

        while True:
            if current_page >= page_limit:
                logger.error(
                    "[CONVERSATIONS REPORT SERVICE] Report %s has more than %s pages. Finishing flowsrun results by contacts retrieval",
                    report.uuid,
                    page_limit,
                )
                raise ValueError("Report has more than %s pages" % page_limit)

            report.refresh_from_db(fields=["status"])

            if report.status != ReportStatus.IN_PROGRESS:
                logger.info(
                    "[CONVERSATIONS REPORT SERVICE] Report %s is not in progress. Finishing flowsrun results by contacts retrieval",
                    report.uuid,
                )
                raise ValueError("Report %s is not in progress" % report.uuid)

            logger.info(
                "[CONVERSATIONS REPORT SERVICE] Retrieving flowsrun results by contacts for page %s for report %s",
                current_page,
                report.uuid,
            )

            paginated_results = (
                self.elasticsearch_service.get_flowsrun_results_by_contacts(
                    project_uuid=report.project.uuid,
                    flow_uuid=flow_uuid,
                    start_date=start_date,
                    end_date=end_date,
                    op_field=op_field,
                    page_size=page_size,
                    page_number=current_page,
                )
            )

            contacts = paginated_results.get("contacts", [])

            if len(contacts) == 0 or contacts == [{}]:
                break

            data.extend(paginated_results["contacts"])
            current_page += 1

        return data

    def get_resolutions_worksheet(
        self,
        report: Report,
        start_date: datetime,
        end_date: datetime,
    ) -> ConversationsReportWorksheet:
        """
        Get the resolutions worksheet.
        """
        events = self.get_datalake_events(
            report=report,
            project=report.project.uuid,
            date_start=start_date,
            date_end=end_date,
            event_name="weni_nexus_data",
            key="conversation_classification",
        )

        with override(report.requested_by.language):
            worksheet_name = gettext("Resolutions")

            resolutions_label = gettext("Resolution")
            date_label = gettext("Date")

            resolved_label = gettext("Optimized Resolutions")
            unresolved_label = gettext("Other conclusions")

        if len(events) == 0:
            return ConversationsReportWorksheet(
                name=worksheet_name,
                data=[],
            )

        data = []

        for event in events:
            data.append(
                {
                    "URN": event.get("contact_urn", ""),
                    resolutions_label: (
                        resolved_label
                        if event.get("value") == "resolved"
                        else unresolved_label
                    ),
                    date_label: (
                        self._format_date(event.get("date", ""))
                        if event.get("date")
                        else ""
                    ),
                }
            )

        return ConversationsReportWorksheet(
            name=worksheet_name,
            data=data,
        )
