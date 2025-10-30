from __future__ import annotations

import django_filters as filters


class UUIDInFilter(filters.BaseInFilter, filters.UUIDFilter):
    pass


class HumanSupportFilterSet(filters.FilterSet):
    project_uuid = filters.UUIDFilter(required=False)
    sectors = UUIDInFilter(required=False)
    queues = UUIDInFilter(required=False)
    tags = UUIDInFilter(required=False)
    page_size = filters.NumberFilter(required=False)
    cursor = filters.CharFilter(required=False)

    class Meta:
        fields = [
            "project_uuid",
            "sectors",
            "queues",
            "tags",
            "page_size",
            "cursor",
        ]
