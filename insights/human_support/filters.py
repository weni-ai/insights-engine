from __future__ import annotations

import django_filters as filters


class UUIDInFilter(filters.BaseInFilter, filters.UUIDFilter):
    pass


class HumanSupportFilterSet(filters.FilterSet):
    project_uuid = filters.UUIDFilter(required=False)
    sectors = UUIDInFilter(required=False)
    queues = UUIDInFilter(required=False)
    tags = UUIDInFilter(required=False)
    start_date = filters.IsoDateTimeFilter(required=False)
    end_date = filters.IsoDateTimeFilter(required=False)

    class Meta:
        fields = [
            "project_uuid",
            "sectors",
            "queues",
            "tags",
            "start_date",
            "end_date",
        ]