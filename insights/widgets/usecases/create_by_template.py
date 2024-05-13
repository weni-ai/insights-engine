from dataclasses import dataclass
from typing import Dict, List, Union

from django.db import transaction

from insights.widgets.models import Report, Widget

from .exceptions import InvalidWidgetObject


@dataclass
class WidgetCreationDTO:
    dashboard: str
    name: str
    w_type: str
    source: str
    position: Dict[str, int]
    config: Dict[str, Union[str, int, float, bool, None]]
    report: Dict[str, Union[str, int, float, bool, None]]


class WidgetCreationUseCase:

    def create_widgets(self, widget_dtos: List[WidgetCreationDTO]):
        if not widget_dtos:
            raise ValueError("widget list cannot be empty!")

        widgets_to_create = []
        reports_to_create = []
        try:
            with transaction.atomic():
                for widget_dto in widget_dtos:
                    widget = Widget(
                        dashboard=widget_dto.dashboard,
                        name=widget_dto.name,
                        w_type=widget_dto.w_type,
                        source=widget_dto.source,
                        position=widget_dto.position,
                        config=widget_dto.config,
                    )
                    widgets_to_create.append(widget)

                    if widget_dto.report:
                        report = Report(
                            widget=widget,
                            **widget_dto.report,
                        )
                        reports_to_create.append(report)

                Widget.objects.bulk_create(widgets_to_create)
                if reports_to_create:
                    Report.objects.bulk_create(reports_to_create)
        except Exception as exception:
            raise InvalidWidgetObject(f"Error creating widget: {exception}")
