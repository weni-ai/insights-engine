from datetime import datetime
import time
import io
import json
from uuid import UUID
import logging
from abc import ABC, abstractmethod
import pytz
import zipfile
import boto3
import uuid

from django.utils.crypto import get_random_string
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext, override
from django.utils import translation, timezone
from sentry_sdk import capture_exception

from insights.metrics.conversations.enums import ConversationType
from insights.metrics.conversations.reports.available_widgets import (
    get_csat_ai_widget,
    get_csat_human_widget,
    get_custom_widgets,
    get_nps_ai_widget,
    get_nps_human_widget,
)
from insights.metrics.conversations.reports.dataclass import (
    AvailableReportWidgets,
    ConversationsReportFile,
    ConversationsReportWorksheet,
)
from insights.metrics.conversations.reports.file_processors import get_file_processor
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.reports.models import Report
from insights.reports.choices import ReportStatus, ReportFormat, ReportSource
from insights.users.models import User
from insights.projects.models import Project
from insights.sources.dl_events.clients import BaseDataLakeEventsClient
from insights.metrics.conversations.integrations.elasticsearch.services import (
    ConversationsElasticsearchService,
)
from insights.widgets.models import Widget
from insights.sources.cache import CacheClient


logger = logging.getLogger(__name__)


CSV_FILE_NAME_MAX_LENGTH = 31
XLSX_FILE_NAME_MAX_LENGTH = 31
XLSX_WORKSHEET_NAME_MAX_LENGTH = 31


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
    def zip_files(
        self, files: list[ConversationsReportFile]
    ) -> ConversationsReportFile:
        """
        Zip the files into a single file.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def upload_file_to_s3(self, file: ConversationsReportFile) -> str:
        """
        Upload the file to S3.
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

    @abstractmethod
    def get_topics_distribution_worksheet(
        self,
        report: Report,
        start_date: datetime,
        end_date: datetime,
        conversation_type: ConversationType,
    ) -> ConversationsReportWorksheet:
        """
        Get the topics distribution worksheet.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def get_csat_ai_worksheet(
        self, report: Report, start_date: datetime, end_date: datetime
    ) -> ConversationsReportWorksheet:
        """
        Get the csat ai worksheet.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def get_nps_ai_worksheet(
        self, report: Report, start_date: datetime, end_date: datetime
    ) -> ConversationsReportWorksheet:
        """
        Get nps ai worksheet.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def get_flowsrun_results_by_contacts(
        flow_uuid: str,
        start_date: str,
        end_date: str,
        op_field: str,
    ) -> list[dict]:
        """
        Get flowsrun results by contacts.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def get_csat_human_worksheet(
        self, report: Report, start_date: str, end_date: str
    ) -> ConversationsReportWorksheet:
        """
        Get csat human worksheet.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def get_nps_human_worksheet(
        self, report: Report, start_date: str, end_date: str
    ) -> ConversationsReportWorksheet:
        """
        Get nps human worksheet.
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
        cache_client: CacheClient,
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
        self.cache_client = cache_client
        self.elastic_page_size = elastic_page_size
        self.elastic_page_limit = elastic_page_limit

        self.cache_keys = {}

    def _add_cache_key(self, report_uuid: UUID, cache_key: str) -> None:
        """
        Add cache key to report.
        """
        report_uuid = str(report_uuid)

        if report_uuid not in self.cache_keys:
            self.cache_keys[report_uuid] = set()

        self.cache_keys[report_uuid].add(cache_key)

    def _clear_cache_keys(self, report_uuid: UUID) -> None:
        """
        Clear cache keys for report.
        """
        report_uuid = str(report_uuid)

        if report_uuid in self.cache_keys:
            for cache_key in self.cache_keys[report_uuid]:
                self.cache_client.delete(cache_key)

            del self.cache_keys[report_uuid]

    def zip_files(
        self, files: list[ConversationsReportFile]
    ) -> ConversationsReportFile:
        """
        Zip the files into a single file.
        """
        names_used = set()

        with io.BytesIO() as zip_buffer:
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                for file in files:
                    name = file.name

                    if name in names_used:
                        max_attempts = 10
                        resolved = False

                        for attempt in range(max_attempts):
                            random_str = get_random_string(5)

                            candidate_name = f"{random_str}_{name}"

                            if candidate_name not in names_used:
                                name = candidate_name
                                resolved = True
                                break

                        if not resolved:
                            raise ValueError("Failed to generate a unique name")

                    names_used.add(name)
                    zip_file.writestr(name, file.content)

            zip_content = zip_buffer.getvalue()

        return ConversationsReportFile(
            name="conversations_report.zip", content=zip_content
        )

    def upload_file_to_s3(self, file: ConversationsReportFile):
        """
        Upload the file to S3.
        """
        s3 = boto3.client("s3")
        extension = file.name.split(".")[-1]
        obj_key = f"reports/conversations/{str(uuid.uuid4())}.{extension}"

        # Wrap content in BytesIO to make it file-like
        file_obj = io.BytesIO(file.content)

        s3.upload_fileobj(
            file_obj,
            settings.S3_BUCKET_NAME,
            obj_key,
        )

        return obj_key

    def get_presigned_url(self, obj_key: str) -> str:
        """
        Get the presigned url for the file.
        """
        s3 = boto3.client("s3")

        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET_NAME, "Key": obj_key},
            ExpiresIn=settings.CONVERSATIONS_REPORT_PRESIGNED_URL_EXPIRATION_TIME,
        )

    def send_email(
        self,
        report: Report,
        files: list[ConversationsReportFile],
        is_error: bool = False,
        event_id: str | None = None,
    ) -> None:
        """
        Send the email for the conversations report.
        """
        try:
            with translation.override(report.requested_by.language):
                subject = _("Conversations dashboard report")

                if len(files) > 1:
                    reports_file = self.zip_files(files)
                elif len(files) == 1:
                    reports_file = files[0]
                else:
                    reports_file = None

                file_link = None

                if reports_file and settings.USE_S3:
                    obj_key = self.upload_file_to_s3(reports_file)
                    file_link = self.get_presigned_url(obj_key)
                    reports_file = None

                if is_error:
                    body = render_to_string(
                        "metrics/conversations/emails/report_failed.html",
                        {
                            "project_name": report.project.name,
                            "event_id": event_id,
                        },
                    )
                else:
                    body = render_to_string(
                        "metrics/conversations/emails/report_is_ready.html",
                        {
                            "project_name": report.project.name,
                            "file_link": file_link,
                        },
                    )

                email = EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[report.requested_by.email],
                )
                email.content_subtype = "html"

                if reports_file and not settings.USE_S3:
                    email.attach(
                        reports_file.name,
                        reports_file.content,
                        "application/zip",
                    )

                email.send(fail_silently=False)
        except Exception as e:
            logger.error(
                "[CONVERSATIONS REPORT SERVICE] Failed to send email for conversations report. "
                "Report UUID: %s, Project UUID: %s, Project Name: %s, "
                "Recipient Email: %s, Is Error Report: %s, Event ID: %s, "
                "Exception Type: %s, Exception Message: %s",
                report.uuid,
                report.project.uuid,
                report.project.name,
                report.requested_by.email,
                is_error,
                event_id,
                type(e).__name__,
                str(e),
                exc_info=True,
            )

            return None

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

    def _update_report_status(self, report: Report) -> Report:
        """
        Update the status of a report.
        """
        fields_to_update = []

        if report.status == ReportStatus.PENDING:
            report.status = ReportStatus.IN_PROGRESS
            fields_to_update.append("status")

        if not report.started_at:
            # If the report generation was interrupted and restarted
            # the field will be already set. Otherwise, we set it to the current time
            report.started_at = timezone.now()
            fields_to_update.append("started_at")

        if fields_to_update:
            report.save(update_fields=fields_to_update)

        return report

    def _validate_dates(self, report: Report) -> tuple[datetime, datetime]:
        """
        Validate the dates of a report.
        """
        filters = report.filters or {}

        start_date = filters.get("start")
        end_date = filters.get("end")

        if not start_date or not end_date:
            raise ValueError(
                "Start date or end date is missing for report %s" % report.uuid
            )

        return start_date, end_date

    def _get_worksheets(
        self, report: Report, start_date: datetime, end_date: datetime
    ) -> list[ConversationsReportWorksheet]:
        """
        Get the worksheets for a report.
        """
        source_config = report.source_config or {}
        sections = source_config.get("sections", [])
        custom_widgets = source_config.get("custom_widgets", [])
        worksheets = []

        worksheets_mapping = {
            "RESOLUTIONS": (
                self.get_resolutions_worksheet,
                {"report": report, "start_date": start_date, "end_date": end_date},
            ),
            "TRANSFERRED": (
                self.get_transferred_to_human_worksheet,
                {"report": report, "start_date": start_date, "end_date": end_date},
            ),
            "TOPICS_AI": (
                self.get_topics_distribution_worksheet,
                {
                    "report": report,
                    "start_date": start_date,
                    "end_date": end_date,
                    "conversation_type": ConversationType.AI,
                },
            ),
            "TOPICS_HUMAN": (
                self.get_topics_distribution_worksheet,
                {
                    "report": report,
                    "start_date": start_date,
                    "end_date": end_date,
                    "conversation_type": ConversationType.HUMAN,
                },
            ),
            "CSAT_AI": (
                self.get_csat_ai_worksheet,
                {"report": report, "start_date": start_date, "end_date": end_date},
            ),
            "NPS_AI": (
                self.get_nps_ai_worksheet,
                {"report": report, "start_date": start_date, "end_date": end_date},
            ),
            "CSAT_HUMAN": (
                self.get_csat_human_worksheet,
                {"report": report, "start_date": start_date, "end_date": end_date},
            ),
            "NPS_HUMAN": (
                self.get_nps_human_worksheet,
                {"report": report, "start_date": start_date, "end_date": end_date},
            ),
        }

        for section, (worksheet_function, worksheet_args) in worksheets_mapping.items():
            if section in sections:
                worksheets.append(worksheet_function(**worksheet_args))

        if custom_widgets:
            widgets = Widget.objects.filter(
                uuid__in=custom_widgets, dashboard__project=report.project
            )

            for widget in widgets:
                worksheets.append(
                    self.get_custom_widget_worksheet(
                        report,
                        widget,
                        start_date,
                        end_date,
                    )
                )

        return worksheets

    def generate(self, report: Report) -> None:
        """
        Start the generation of a conversations report.
        """
        logger.info(
            "[CONVERSATIONS REPORT SERVICE] Starting generation of conversations report %s",
            report.uuid,
        )

        report = self._update_report_status(report)
        file_processor = get_file_processor(report.format)

        try:
            start_date, end_date = self._validate_dates(report)

            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)

            logger.info(
                "[CONVERSATIONS REPORT SERVICE] Start date: %s, End date: %s",
                start_date,
                end_date,
            )

            worksheets = self._get_worksheets(report, start_date, end_date)
            files = file_processor.process(report=report, worksheets=worksheets)

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
            self._clear_cache_keys(report.uuid)

            event_id = capture_exception(e)

            self.send_email(report, [], is_error=True, event_id=event_id)

            return None

        report.refresh_from_db(fields=["config"])

        config = report.config or {}
        if config.get("interrupted"):
            logger.info(
                "[CONVERSATIONS REPORT SERVICE] Report %s is interrupted. Finishing generation",
                report.uuid,
            )
            return

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
            self._clear_cache_keys(report.uuid)
            raise e

        logger.info(
            "[CONVERSATIONS REPORT SERVICE] Email for conversations report %s sent to %s",
            report.uuid,
            report.requested_by.email,
        )

        report.status = ReportStatus.READY
        report.completed_at = timezone.now()
        report.save(update_fields=["status", "completed_at"])

        self._clear_cache_keys(report.uuid)

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
        kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)
        cache_key = f"datalake_events:{report.uuid}:{kwargs_str}"

        if cached_events := self.cache_client.get(cache_key):
            try:
                cached_events = json.loads(cached_events)
                self._add_cache_key(report.uuid, cache_key)
                return cached_events
            except Exception as e:
                logger.error(
                    "[CONVERSATIONS REPORT SERVICE] Failed to deserialize cached events for report %s. Error: %s",
                    report.uuid,
                    e,
                )

        limit = self.events_limit_per_page
        offset = 0

        events = []

        current_page = 1
        page_limit = self.page_limit

        date_start = kwargs.get("date_start")
        date_end = kwargs.get("date_end")

        if date_start and isinstance(date_start, datetime):
            kwargs["date_start"] = date_start.isoformat()

        if date_end and isinstance(date_end, datetime):
            kwargs["date_end"] = date_end.isoformat()

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
                print("paginated_events", paginated_events)
                break

            events.extend(paginated_events)
            offset += limit
            current_page += 1

        self.cache_client.set(
            cache_key, json.dumps(events), ex=settings.REPORT_GENERATION_TIMEOUT
        )
        self._add_cache_key(report.uuid, cache_key)

        return events

    def _format_date(self, original_date: str | int, report: Report) -> str:
        """
        Format the date.
        """

        formats = ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S"]

        datetime_date = None

        if isinstance(original_date, int):
            if len(str(original_date)) == 13:
                # If the date is in milliseconds, convert it to seconds
                original_date = original_date // 1000

            try:
                datetime_date = datetime.fromtimestamp(original_date)
            except Exception:
                pass

        for _format in formats:
            try:
                datetime_date = datetime.strptime(original_date, _format)
                break
            except Exception:
                continue

        if not datetime_date:
            try:
                datetime_date = datetime.fromisoformat(original_date)
            except Exception:
                pass

        if datetime_date:
            tz_name = report.project.timezone

            if tz_name:
                tz = pytz.timezone(tz_name)
                datetime_date = datetime_date.astimezone(tz)

            return datetime_date.strftime("%d/%m/%Y %H:%M:%S")

        # Return the original date as a fallback
        # if everything fails
        return str(original_date)

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
            table="conversation_classification",
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
                        self._format_date(event.get("date", ""), report)
                        if event.get("date")
                        else ""
                    ),
                }
            )

        setattr(self, "_conversation_classification_events_cache", events)

        if len(data) == 0:
            data = [
                {
                    "URN": "",
                    resolutions_label: "",
                    date_label: "",
                }
            ]

        return ConversationsReportWorksheet(
            name=worksheet_name,
            data=data,
        )

    def get_transferred_to_human_worksheet(
        self,
        report: Report,
        start_date: datetime,
        end_date: datetime,
    ) -> ConversationsReportWorksheet:
        """
        Get the transferred to human worksheet.
        """
        if hasattr(self, "_conversation_classification_events_cache"):
            events = getattr(self, "_conversation_classification_events_cache")
        else:
            events = self.get_datalake_events(
                report=report,
                project=report.project.uuid,
                date_start=start_date,
                date_end=end_date,
                event_name="weni_nexus_data",
                key="conversation_classification",
                table="conversation_classification",
                metadata_key="human_support",
                metadata_value="true",
            )

        with override(report.requested_by.language):
            worksheet_name = gettext("Transferred to Human")

            date_label = gettext("Date")

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
                    date_label: (
                        self._format_date(event.get("date", ""), report)
                        if event.get("date")
                        else ""
                    ),
                }
            )

        if len(data) == 0:
            data = [
                {
                    "URN": "",
                    date_label: "",
                }
            ]

        return ConversationsReportWorksheet(
            name=worksheet_name,
            data=data,
        )

    def _get_topics_data(self, report: Report) -> dict:
        """
        Get the topics data from Nexus and organize it.
        """
        nexus_topics_data = self.metrics_service.get_topics(report.project.uuid)

        topics_data = {}

        for topic_data in nexus_topics_data:
            topic_uuid = str(topic_data.get("uuid"))
            topics_data[topic_uuid] = {
                "name": topic_data.get("name"),
                "uuid": topic_uuid,
                "subtopics": {},
            }

            if not topic_data.get("subtopic"):
                continue

            for subtopic_data in topic_data.get("subtopic", []):
                subtopic_uuid = str(subtopic_data.get("uuid"))
                topics_data[topic_uuid]["subtopics"][subtopic_uuid] = {
                    "name": subtopic_data.get("name"),
                    "uuid": subtopic_uuid,
                }

        return topics_data

    def _process_topic_event_data(
        self, event: dict, topics_data: dict, unclassified_label: str
    ) -> dict:
        """
        Process the topic and subtopic data.
        """
        try:
            metadata = json.loads(event.get("metadata", "{}"))
        except Exception as e:
            logger.error("Error parsing metadata for event %s: %s", event.get("id"), e)
            capture_exception(e)
            return None, None

        topic_name = event.get("value")
        subtopic_name = metadata.get("subtopic")

        topic_uuid = (
            str(metadata.get("topic_uuid")) if metadata.get("topic_uuid") else None
        )
        subtopic_uuid = (
            str(metadata.get("subtopic_uuid"))
            if metadata.get("subtopic_uuid")
            else None
        )

        if not topic_uuid or topic_uuid not in topics_data:
            topic_name = unclassified_label

        if (
            topic_uuid
            and topic_uuid in topics_data
            and not subtopic_uuid
            and subtopic_uuid not in topics_data[topic_uuid]["subtopics"]
        ) or (not topic_uuid or topic_uuid not in topics_data):
            subtopic_name = unclassified_label

        return topic_name, subtopic_name

    def get_topics_distribution_worksheet(
        self,
        report: Report,
        start_date: datetime,
        end_date: datetime,
        conversation_type: ConversationType,
    ) -> ConversationsReportWorksheet:
        """
        Get the topics distribution worksheet.
        """
        topics_data = self._get_topics_data(report)

        human_support = (
            "true" if conversation_type == ConversationType.HUMAN else "false"
        )
        events = self.get_datalake_events(
            report=report,
            project=report.project.uuid,
            date_start=start_date,
            date_end=end_date,
            event_name="weni_nexus_data",
            key="topics",
            metadata_key="human_support",
            metadata_value=human_support,
            table="topics",
        )

        with override(report.requested_by.language or "en"):
            worksheet_name = (
                gettext("Topics Distribution AI")
                if conversation_type == ConversationType.AI
                else gettext("Topics Distribution Human")
            )
            date_label = gettext("Date")
            topic_label = gettext("Topic")
            subtopic_label = gettext("Subtopic")
            unclassified_label = gettext("Unclassified")

        results_data = []

        for event in events:
            topic_name, subtopic_name = self._process_topic_event_data(
                event, topics_data, unclassified_label
            )

            if not topic_name or not subtopic_name:
                continue

            results_data.append(
                {
                    "URN": event.get("contact_urn"),
                    topic_label: topic_name,
                    subtopic_label: subtopic_name,
                    date_label: (
                        self._format_date(event.get("date"), report)
                        if event.get("date")
                        else ""
                    ),
                }
            )

        if len(results_data) == 0:
            results_data = [
                {
                    "URN": "",
                    topic_label: "",
                    subtopic_label: "",
                    date_label: "",
                }
            ]

        return ConversationsReportWorksheet(
            name=worksheet_name,
            data=results_data,
        )

    def get_csat_ai_worksheet(
        self, report: Report, start_date: datetime, end_date: datetime
    ) -> ConversationsReportWorksheet:
        """
        Get the csat ai worksheet.
        """
        agent_uuid = report.source_config.get("csat_ai_agent_uuid", None)

        if not agent_uuid:
            raise ValueError("Agent UUID is required in the report source config")

        events = self.get_datalake_events(
            report,
            project=str(report.project.uuid),
            date_start=start_date,
            date_end=end_date,
            metadata_key="agent_uuid",
            metadata_value=agent_uuid,
            key="weni_csat",
            event_name="weni_nexus_data",
            table="weni_csat",
        )

        with override(report.requested_by.language or "en"):
            worksheet_name = gettext("CSAT AI")
            date_label = gettext("Date")
            rating_label = gettext("Rating")

        data = []

        ratings = {"1", "2", "3", "4", "5"}

        for event in events:
            if event.get("value") not in ratings:
                continue

            data.append(
                {
                    "URN": event.get("contact_urn"),
                    date_label: self._format_date(event.get("date"), report),
                    rating_label: event.get("value"),
                }
            )

        if len(data) == 0:
            data = [
                {
                    "URN": "",
                    date_label: "",
                    rating_label: "",
                }
            ]

        return ConversationsReportWorksheet(
            name=worksheet_name,
            data=data,
        )

    def get_nps_ai_worksheet(
        self, report: Report, start_date: datetime, end_date: datetime
    ) -> ConversationsReportWorksheet:
        """
        Get nps ai worksheet
        """

        agent_uuid = report.source_config.get("nps_ai_agent_uuid", None)

        if not agent_uuid:
            raise ValueError("Agent UUID is required in the report source config")

        events = self.get_datalake_events(
            report,
            project=str(report.project.uuid),
            date_start=start_date,
            date_end=end_date,
            metadata_key="agent_uuid",
            metadata_value=agent_uuid,
            key="weni_nps",
            event_name="weni_nexus_data",
            table="weni_nps",
        )

        with override(report.requested_by.language or "en"):
            worksheet_name = gettext("NPS AI")
            date_label = gettext("Date")
            rating_label = gettext("Rating")

        data = []
        ratings = {str(n): 0 for n in range(0, 11)}

        for event in events:
            if event.get("value") not in ratings:
                continue

            data.append(
                {
                    "URN": event.get("contact_urn"),
                    date_label: (
                        self._format_date(event.get("date"), report)
                        if event.get("date")
                        else ""
                    ),
                    rating_label: event.get("value"),
                }
            )

        if len(data) == 0:
            data = [
                {
                    "URN": "",
                    date_label: "",
                    rating_label: "",
                }
            ]

        return ConversationsReportWorksheet(name=worksheet_name, data=data)

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
        cache_key = f"flowsrun_results_by_contacts:{report.uuid}:{flow_uuid}:{start_date}:{end_date}:{op_field}"

        if cached_results := self.cache_client.get(cache_key):
            try:
                cached_results = json.loads(cached_results)
                self._add_cache_key(report.uuid, cache_key)
            except Exception as e:
                logger.error(
                    "[CONVERSATIONS REPORT SERVICE] Failed to deserialize cached results for report %s. Error: %s",
                    report.uuid,
                    e,
                )

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

        self.cache_client.set(
            cache_key, json.dumps(data), ex=settings.REPORT_GENERATION_TIMEOUT
        )
        self._add_cache_key(report.uuid, cache_key)

        return data

    def get_csat_human_worksheet(
        self, report: Report, start_date: str, end_date: str
    ) -> ConversationsReportWorksheet:
        """
        Get csat human worksheet.
        """
        # [STAGING] Mock for the staging environment
        mock_urns = ["55988776655", "55988776656", "55988776657"]

        data = []

        with override(report.requested_by.language or "en"):
            worksheet_name = gettext("CSAT Human")
            date_label = gettext("Date")
            rating_label = gettext("Rating")

        for mock_urn in mock_urns:
            data.append(
                {
                    "URN": mock_urn,
                    date_label: self._format_date(
                        "2025-01-01T00:00:00.000000Z", report
                    ),
                    rating_label: "5",
                }
            )

        return ConversationsReportWorksheet(
            name=worksheet_name,
            data=data,
        )

        flow_uuid = report.source_config.get("csat_human_flow_uuid", None)
        op_field = report.source_config.get("csat_human_op_field", None)

        missing_fields = []

        if not flow_uuid:
            missing_fields.append("flow_uuid")

        if not op_field:
            missing_fields.append("op_field")

        if missing_fields:
            logger.error(
                "[CONVERSATIONS REPORT SERVICE] Missing fields for report %s: %s",
                report.uuid,
                ", ".join(missing_fields),
            )
            raise ValueError(
                "Missing fields for report %s: %s"
                % (report.uuid, ", ".join(missing_fields))
            )

        docs = self.get_flowsrun_results_by_contacts(
            report=report,
            flow_uuid=flow_uuid,
            start_date=start_date,
            end_date=end_date,
            op_field=op_field,
        )

        with override(report.requested_by.language or "en"):
            worksheet_name = gettext("CSAT Human")
            date_label = gettext("Date")
            rating_label = gettext("Rating")

        data = []

        for doc in docs:
            if doc["op_field_value"] is None:
                continue

            data.append(
                {
                    "URN": doc["urn"],
                    date_label: self._format_date(doc["modified_on"], report),
                    rating_label: doc["op_field_value"],
                }
            )

        if len(data) == 0:
            data = [
                {
                    "URN": "",
                    date_label: "",
                    rating_label: "",
                }
            ]

        return ConversationsReportWorksheet(
            name=worksheet_name,
            data=data,
        )

    def get_nps_human_worksheet(
        self, report: Report, start_date: str, end_date: str
    ) -> ConversationsReportWorksheet:
        """
        Get nps human worksheet.
        """
        # [STAGING] Mock for the staging environment
        mock_urns = ["55988776655", "55988776656", "55988776657"]

        data = []

        with override(report.requested_by.language or "en"):
            worksheet_name = gettext("NPS Human")
            date_label = gettext("Date")
            rating_label = gettext("Rating")

        for mock_urn in mock_urns:
            data.append(
                {
                    "URN": mock_urn,
                    date_label: self._format_date(
                        "2025-01-01T00:00:00.000000Z", report
                    ),
                    rating_label: "10",
                }
            )

        return ConversationsReportWorksheet(
            name=worksheet_name,
            data=data,
        )
        flow_uuid = report.source_config.get("nps_human_flow_uuid", None)
        op_field = report.source_config.get("nps_human_op_field", None)

        missing_fields = []

        if not flow_uuid:
            missing_fields.append("flow_uuid")

        if not op_field:
            missing_fields.append("op_field")

        if missing_fields:
            logger.error(
                "[CONVERSATIONS REPORT SERVICE] Missing fields for report %s: %s",
                report.uuid,
                ", ".join(missing_fields),
            )
            raise ValueError(
                "Missing fields for report %s: %s"
                % (report.uuid, ", ".join(missing_fields))
            )

        docs = self.get_flowsrun_results_by_contacts(
            report=report,
            flow_uuid=flow_uuid,
            start_date=start_date,
            end_date=end_date,
            op_field=op_field,
        )

        with override(report.requested_by.language or "en"):
            worksheet_name = gettext("NPS Human")
            date_label = gettext("Date")
            rating_label = gettext("Rating")

        data = []

        for doc in docs:
            if doc["op_field_value"] is None:
                continue

            data.append(
                {
                    "URN": doc["urn"],
                    date_label: self._format_date(doc["modified_on"], report),
                    rating_label: doc["op_field_value"],
                }
            )

        if len(data) == 0:
            data = [
                {
                    "URN": "",
                    date_label: "",
                    rating_label: "",
                }
            ]

        return ConversationsReportWorksheet(
            name=worksheet_name,
            data=data,
        )

    def get_custom_widget_worksheet(
        self,
        report: Report,
        widget: Widget,
        start_date: datetime,
        end_date: datetime,
    ) -> ConversationsReportWorksheet:
        """
        Get custom widgets results.
        """
        datalake_config = widget.config.get("datalake_config", {})
        key = datalake_config.get("key", "")
        agent_uuid = datalake_config.get("agent_uuid", "")

        if not key or not agent_uuid:
            raise ValueError("Key or agent_uuid is missing in the widget config")

        events = self.get_datalake_events(
            report,
            key=key,
            event_name="weni_nexus_data",
            project=report.project.uuid,
            date_start=start_date,
            date_end=end_date,
            metadata_key="agent_uuid",
            metadata_value=agent_uuid,
        )

        worksheet_name = widget.name

        with override(report.requested_by.language or "en"):
            date_label = gettext("Date")
            value_label = gettext("Value")

        data = []

        for event in events:
            data.append(
                {
                    "URN": event.get("contact_urn"),
                    date_label: self._format_date(event.get("date"), report),
                    value_label: event.get("value"),
                }
            )

        if len(data) == 0:
            data = [
                {
                    "URN": "",
                    date_label: "",
                    value_label: "",
                }
            ]

        return ConversationsReportWorksheet(
            name=worksheet_name,
            data=data,
        )

    def get_available_widgets(self, project: Project) -> AvailableReportWidgets:
        """
        Get available widgets.
        """
        available_widgets = [
            "RESOLUTIONS",
            "TRANSFERRED",
            "TOPICS_AI",
            "TOPICS_HUMAN",
        ]

        special_widgets_get_functions = [
            (get_csat_ai_widget, "CSAT_AI"),
            (get_csat_human_widget, "CSAT_HUMAN"),
            (get_nps_ai_widget, "NPS_AI"),
            (get_nps_human_widget, "NPS_HUMAN"),
        ]

        for get_function, section in special_widgets_get_functions:
            if get_function(project):
                available_widgets.append(section)

        custom_widgets = get_custom_widgets(project)

        return AvailableReportWidgets(
            sections=available_widgets,
            custom_widgets=custom_widgets,
        )
