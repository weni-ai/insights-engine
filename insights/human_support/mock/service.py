from insights.human_support.mock.sources import (
    MockAverageOrderValueSource,
    MockChannelRevenueSaleSource,
    MockRepresentativePerformanceSource,
    MockRevenueSource,
    MockSalesFunnelSource,
    REPRESENTATIVE_EMAILS,
)
from insights.human_support.services import HumanSupportDashboardService
from insights.projects.models import Project


def mocked_human_support_dashboard_service(
    project: Project,
) -> HumanSupportDashboardService:
    return HumanSupportDashboardService(
        project=project,
        revenue_source=MockRevenueSource(),
        average_order_value_source=MockAverageOrderValueSource(),
        sales_funnel_source=MockSalesFunnelSource(),
        channel_revenue_sale_source=MockChannelRevenueSaleSource(),
        representative_performance_source=MockRepresentativePerformanceSource(),
    )


def to_sales_data_payload(service: HumanSupportDashboardService, filters: dict) -> dict:
    average_order_value = service.get_average_order_value(filters=filters)
    total_revenue = service.get_total_revenue(filters=filters)

    return {
        "average_order_value": average_order_value["value"],
        "total_revenue": {
            "value": total_revenue["value"],
            "last_period_value": total_revenue["previous_value"],
            "variation": total_revenue["increase_percentage"],
        },
    }


def to_purchases_made_payload(
    service: HumanSupportDashboardService, filters: dict
) -> dict:
    funnel = service.get_sales_funnel(filters=filters)

    return {
        "leads_captured": {
            "value": funnel["leads_captured"]["full_value"],
            "percentage": funnel["leads_captured"]["value"],
        },
        "purchases_made": {
            "value": funnel["purchases_made"]["full_value"],
            "percentage": funnel["purchases_made"]["value"],
        },
    }


def to_per_channel_results(
    service: HumanSupportDashboardService, filters: dict
) -> list[dict]:
    data = service.get_channel_revenue_sale(filters=filters)
    return [
        {
            "channel_name": row["channel"],
            "total_value": row["value"],
            "percentage": row["percentage"],
        }
        for row in data["results"]
    ]


def _trend_payload(trend: float) -> dict:
    if trend < 0:
        variation_type = "DECREASE"
    else:
        variation_type = "INCREASE"

    return {"value": trend, "variation_type": variation_type}


def to_per_representative_results(
    service: HumanSupportDashboardService, filters: dict
) -> list[dict]:
    data = service.get_performance_by_representative(filters=filters)
    results = []

    for row in data["results"]:
        name = row["representative"]
        results.append(
            {
                "representative": {
                    "name": name,
                    "email": REPRESENTATIVE_EMAILS.get(name, ""),
                },
                "conversations": row["conversations"],
                "sales": row["sales"],
                "conversions": row["conversion"],
                "revenue": row["revenue"],
                "average_order_value": row["average_order_value"],
                "trend": _trend_payload(row["trend"]),
            }
        )

    return results
