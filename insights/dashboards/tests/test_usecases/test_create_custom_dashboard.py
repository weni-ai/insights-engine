import pytest
from django.db.utils import IntegrityError

from insights.dashboards.models import Dashboard
from insights.projects.usecases.dashboard_dto import FlowsDashboardCreationDTO
from insights.dashboards.usecases.flows_dashboard_creation import CreateFlowsDashboard
from rest_framework.test import APIClient
from insights.projects.models import ProjectAuth, Roles
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_create_custom_dashboard(create_project):
    project = create_project
    name = "Custom Flows Dashboard"

    dto_object = FlowsDashboardCreationDTO(
        project=project,
        dashboard_name=name,
        funnel_amount=3,
        currency_type="real",
    )
    dashboard_creator = CreateFlowsDashboard(params=dto_object)

    assert dashboard_creator.dashboard_name == "Custom Flows Dashboard"


@pytest.mark.django_db
def test_update_dashboard_success(
    create_user, create_project, create_editable_dashboard
):
    client = APIClient()
    auth = ProjectAuth.objects.create(
        user=create_user, project=create_project, role=Roles.ADMIN
    )
    client.force_authenticate(user=auth.user)
    dashboard = create_editable_dashboard

    url = (
        reverse("dashboard-detail", kwargs={"pk": dashboard.pk})
        + f"?project={create_project.pk}"
    )
    data = {"name": "Updated Dashboard"}
    response = client.patch(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK

    dashboard.refresh_from_db()
    assert dashboard.name == "Updated Dashboard"


@pytest.mark.django_db
def test_update_no_editable_dashboard(
    create_user, create_project, create_no_editable_dashboard
):
    client = APIClient()
    auth = ProjectAuth.objects.create(
        user=create_user, project=create_project, role=Roles.ADMIN
    )
    client.force_authenticate(user=auth.user)
    dashboard = create_no_editable_dashboard

    url = (
        reverse("dashboard-detail", kwargs={"pk": dashboard.pk})
        + f"?project={create_project.pk}"
    )
    data = {"name": "Updated Dashboard"}
    response = client.patch(url, data, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN
