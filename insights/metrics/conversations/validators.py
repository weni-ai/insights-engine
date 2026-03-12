from datetime import datetime, time
import pytz

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from insights.projects.models import Project


class ConversationsDatesValidator:
    def __init__(self, project: Project, start_date: datetime, end_date: datetime):
        self.project = project
        self.start_date = start_date
        self.end_date = end_date

    def validate(self) -> tuple[datetime, datetime]:
        """
        Validate dates
        """
        if self.start_date > self.end_date:
            raise serializers.ValidationError(
                {"start_date": _("Start date must be before end date")},
                code="start_date_after_end_date",
            )

        timezone = (
            pytz.timezone(self.project.timezone) if self.project.timezone else pytz.UTC
        )

        # Convert start_date to datetime at midnight (00:00:00) in project timezone
        start_datetime = datetime.combine(self.start_date.date(), time.min)
        start_datetime = (
            timezone.localize(start_datetime).astimezone(pytz.UTC).replace(tzinfo=None)
        )
        self.start_date = start_datetime

        # Convert end_date to datetime at 23:59:59 in project timezone
        end_datetime = datetime.combine(self.end_date.date(), time(23, 59, 59))
        end_datetime = (
            timezone.localize(end_datetime).astimezone(pytz.UTC).replace(tzinfo=None)
        )
        self.end_date = end_datetime

        return self.start_date, self.end_date
