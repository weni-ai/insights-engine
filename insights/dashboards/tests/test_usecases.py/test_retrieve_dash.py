# test get dashboard
# test get default dashboard
# test list dashboards with and without filters (use parametrized tests)

import pytest

from insights.dashboards.usecases.retrieve_dashboard import (
    DashboardRetrieveUseCase,
)


@pytest.mark.parametrize(
    "pk",
    [
        True,
        False,
    ],
    ids=["retrieve_pk", "retrieve_default"],
)
@pytest.mark.django_db
def test_get_dashboard(pk, create_default_dashboard):
    dash = create_default_dashboard
    filters = {}
    if pk:
        filters["pk"] = dash.pk

    dashboard = DashboardRetrieveUseCase().get(**filters)
    assert dashboard == dash
