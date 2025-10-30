from __future__ import annotations

import django_filters as filters
from datetime import datetime, time
import pytz

class UUIDInFilter(filters.BaseInFilter, filters.UUIDFilter):
    pass


class HumanSupportFilterSet(filters.FilterSet):
    project_uuid = filters.UUIDFilter(required=False)
    sectors = UUIDInFilter(required=False)
    queues = UUIDInFilter(required=False)
    tags = UUIDInFilter(required=False)
    start_date = filters.DateFilter(required=False)
    end_date = filters.DateFilter(required=False)
    agent = filters.UUIDFilter(required=False)
    contact = filters.UUIDFilter(required=False)
    ticket_id = filters.UUIDFilter(required=False)

    class Meta:
        fields = [
            "project_uuid",
            "sectors",
            "queues",
            "tags",
            "start_date",
            "end_date",
            "agent",
            "contact",
            "ticket_id",
        ]

    def apply_project_timezone(self, project):
            """
            Apply project timezone to start_date and end_date
            - start_date: set time to 00:00:00
            - end_date: set time to 23:59:59
            """
            timezone = pytz.timezone(project.timezone) if project.timezone else pytz.UTC
            
            if self.form.cleaned_data.get("start_date"):
                start_date = self.form.cleaned_data["start_date"]
                if isinstance(start_date, datetime):
                    if start_date.tzinfo is not None:
                        start_date = start_date.replace(tzinfo=None)
                    start_date = start_date.date()
                
                start_datetime = datetime.combine(start_date, time.min)
                self.form.cleaned_data["start_date"] = timezone.localize(start_datetime)
            
            if self.form.cleaned_data.get("end_date"):
                end_date = self.form.cleaned_data["end_date"]
                if isinstance(end_date, datetime):
                    if end_date.tzinfo is not None:
                        end_date = end_date.replace(tzinfo=None)
                    end_date = end_date.date()
                
                end_datetime = datetime.combine(end_date, time(23, 59, 59))
                self.form.cleaned_data["end_date"] = timezone.localize(end_datetime)
            
            return self.form.cleaned_data