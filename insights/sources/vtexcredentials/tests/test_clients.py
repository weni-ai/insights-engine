from insights.sources.vtexcredentials.clients import AuthRestClient
from django.conf import settings


def test_url_construction():
    project = 123
    client = AuthRestClient(project)

    expected_url = f"{settings.INTEGRATIONS_URL}/api/v1/apptypes/vtex/integration-details/{project}"

    assert client.url == expected_url
