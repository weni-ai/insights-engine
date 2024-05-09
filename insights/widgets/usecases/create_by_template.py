from dataclasses import dataclass
from typing import Dict, List, Union

from django.db import transaction
from django.db.utils import IntegrityError
from exceptions import InvalidWidgetObject

from insights.widgets.models import Widget


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

        created_widgets = []
        try:
            with transaction.atomic():
                for widget_dto in widget_dtos:
                    widget = Widget.objects.create(
                        dashboard=widget_dto.config,
                        name=widget_dto.name,
                        w_type=widget_dto.w_type,
                        source=widget_dto.source,
                        position=widget_dto.position,
                        config=widget_dto.config,
                        report=widget_dto.report,
                    )
                    created_widgets.append(widget)
        except IntegrityError as exception:
            raise InvalidWidgetObject(f"Error creating widget: {exception}")
