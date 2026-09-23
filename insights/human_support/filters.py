from __future__ import annotations

from datetime import datetime, time

import django_filters as filters
import pytz


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    pass


class UUIDInFilter(filters.BaseInFilter, filters.UUIDFilter):
    def filter(self, qs, value):
        if value:
            if isinstance(value, list):
                value = [str(v) for v in value if v]
            else:
                value = [v.strip() for v in str(value).split(",") if v.strip()]
        return super(filters.BaseInFilter, self).filter(qs, value)


class HumanSupportFilterSet(filters.FilterSet):
    project_uuid = filters.UUIDFilter(required=False)
    sectors = UUIDInFilter(required=False)
    queues = UUIDInFilter(required=False)
    tags = UUIDInFilter(required=False)
    channels = CharInFilter(required=False)
    page_size = filters.NumberFilter(required=False)
    cursor = filters.CharFilter(required=False)
    start_date = filters.DateFilter(required=False)
    end_date = filters.DateFilter(required=False)
    comparison_start_date = filters.DateFilter(required=False)
    comparison_end_date = filters.DateFilter(required=False)
    agent = filters.CharFilter(required=False)
    agent_email = filters.CharFilter(required=False)
    contact = filters.CharFilter(required=False)
    urn = filters.CharFilter(required=False)
    ticket_id = filters.CharFilter(required=False)

    class Meta:
        fields = [
            "project_uuid",
            "sectors",
            "queues",
            "tags",
            "channels",
            "page_size",
            "cursor",
            "start_date",
            "end_date",
            "comparison_start_date",
            "comparison_end_date",
            "agent",
            "agent_email",
            "contact",
            "urn",
            "ticket_id",
        ]

    DATE_RANGE_FIELDS = (
        ("start_date", "end_date"),
        ("comparison_start_date", "comparison_end_date"),
    )

    def _localize_date_bound(self, timezone, field, day_time):
        value = self.form.cleaned_data.get(field)
        if not value:
            return

        if isinstance(value, datetime):
            if value.tzinfo is not None:
                value = value.replace(tzinfo=None)
            value = value.date()

        self.form.cleaned_data[field] = timezone.localize(
            datetime.combine(value, day_time)
        )

    def apply_project_timezone(self, project):
        """
        Apply project timezone to the date range filters
        - start bound: set time to 00:00:00
        - end bound: set time to 23:59:59
        """
        timezone = pytz.timezone(project.timezone) if project.timezone else pytz.UTC

        for start_field, end_field in self.DATE_RANGE_FIELDS:
            self._localize_date_bound(timezone, start_field, time.min)
            self._localize_date_bound(timezone, end_field, time(23, 59, 59))

        return self.form.cleaned_data
