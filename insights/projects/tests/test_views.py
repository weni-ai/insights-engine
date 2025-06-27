from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.projects.models import Project


class BaseProjectViewSetTestCase(APITestCase):
    def get_project(self, uuid: str) -> Response:
        url = reverse("project-detail", kwargs={"pk": uuid})

        return self.client.get(url)


class TestProjectViewSetAsAnonymousUser(BaseProjectViewSetTestCase):
    def test_get_project_as_anonymous_user(self):
        response = self.get_project("123e4567-e89b-12d3-a456-426614174000")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestProjectViewSetAsAuthenticatedUser(BaseProjectViewSetTestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@test.com")
        self.project = Project.objects.create(name="Test Project")

        self.client.force_authenticate(user=self.user)

    @with_project_auth
    def test_get_project_as_authenticated_user(self):
        response = self.get_project(self.project.uuid)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
