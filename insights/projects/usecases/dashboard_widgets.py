from insights.widgets.usecases.widget_dto import WidgetCreationDTO
from insights.widgets.usecases.widget_dto import WidgetCreationDTO


def widgets_list(dashboard_list):
    widget_dto_list = []

    for dashboard in dashboard_list:
        if dashboard.name == "atendimento humano":
            for i in range(4):
                widget = WidgetCreationDTO(
                    dashboard=dashboard,
                    name="atendimento humano",
                    w_type="card",
                    source="",
                    position={"x": i, "y": 0},
                    config={},
                    report={},
                )
                widget_dto_list.append(widget)
            widget = WidgetCreationDTO(
                dashboard=dashboard,
                name="atendimento humano",
                w_type="table",
                source="",
                position={"x": 0, "y": 1},
                config={},
                report={},
            )
            widget_dto_list.append(widget)
            widget = WidgetCreationDTO(
                dashboard=dashboard,
                name="atendimento humano",
                w_type="table group",
                source="",
                position={"x": 0, "y": 2},
                config={},
                report={},
            )
            widget_dto_list.append(widget)

        elif dashboard.name == "jornada do bot":
            for i in range(5):
                widget = WidgetCreationDTO(
                    dashboard=dashboard,
                    name="jornada do bot",
                    w_type="card",
                    source="",
                    position={"x": i, "y": 0},
                    config={},
                    report={},
                )
                widget_dto_list.append(widget)
            widget = WidgetCreationDTO(
                dashboard=dashboard,
                name="jornada do bot",
                w_type="funil",
                source="",
                position={"x": 0, "y": 1},
                config={},
                report={},
            )
            widget_dto_list.append(widget)
            widget = WidgetCreationDTO(
                dashboard=dashboard,
                name="jornada do bot",
                w_type="prompt",
                source="",
                position={"x": 0, "y": 2},
                config={},
                report={},
            )
            widget_dto_list.append(widget)

    return widget_dto_list
