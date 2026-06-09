from uuid import uuid4

from django.test import override_settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from insights.authentication.authentication import User
from insights.authentication.services.jwt_service import JWTService
from insights.authentication.services.tests.test_jwt_service import (
    generate_private_key,
    generate_private_key_pem,
    generate_public_key_pem,
)
from insights.authentication.tests.decorators import with_internal_auth
from insights.projects.models import Project


JWT_PRIVATE_KEY = generate_private_key()
JWT_PRIVATE_KEY_PEM = generate_private_key_pem(JWT_PRIVATE_KEY)
JWT_PUBLIC_KEY_PEM = generate_public_key_pem(JWT_PRIVATE_KEY.public_key())


class BaseTestUpdateProjectVTEXAccountView(APITestCase):
    def update_vtex_account(self, project_uuid, data: dict) -> Response:
        url = f"/v1/internal/projects/{project_uuid}/vtex-account"

        return self.client.patch(url, data, format="json")


class TestUpdateProjectVTEXAccountViewAsAnonymousUser(
    BaseTestUpdateProjectVTEXAccountView
):
    def setUp(self):
        self.project = Project.objects.create(name="Alphabet", vtex_account="abc")

    def test_cannot_update_vtex_account_when_unauthenticated(self):
        response = self.update_vtex_account(self.project.uuid, {"vtex_account": "xyz"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestUpdateProjectVTEXAccountViewAsAuthenticatedUser(
    BaseTestUpdateProjectVTEXAccountView
):
    def setUp(self):
        self.user = User.objects.create(email="example@vtex.com")
        self.project = Project.objects.create(name="Alphabet", vtex_account="abc")
        self.client.force_authenticate(user=self.user)

    def test_cannot_update_vtex_account_when_user_is_not_internal(self):
        response = self.update_vtex_account(self.project.uuid, {"vtex_account": "xyz"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_internal_auth
    def test_can_update_vtex_account_with_internal_authentication(self):
        with self.assertLogs(
            "insights.projects.usecases.update_vtex_account", level="INFO"
        ) as logs:
            response = self.update_vtex_account(
                self.project.uuid, {"vtex_account": "xyz"}
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "project": {
                    "name": self.project.name,
                    "uuid": str(self.project.uuid),
                    "vtex_account": "xyz",
                }
            },
        )

        self.project.refresh_from_db()
        self.assertEqual(self.project.vtex_account, "xyz")

        expected_message = (
            f"[UpdateProjectVTEXAccount] VTEX Account for project "
            f"{self.project.name} ({self.project.uuid}) changed from "
            f"'abc' to 'xyz' by {self.user.email}"
        )
        self.assertIn(expected_message, logs.output[0])

    @with_internal_auth
    def test_cannot_update_vtex_account_with_invalid_body(self):
        response = self.update_vtex_account(self.project.uuid, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["vtex_account"][0].code, "required")

    @with_internal_auth
    def test_cannot_update_vtex_account_with_blank_value(self):
        response = self.update_vtex_account(self.project.uuid, {"vtex_account": ""})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["vtex_account"][0].code, "blank")

    @with_internal_auth
    def test_cannot_update_vtex_account_when_project_does_not_exist(self):
        response = self.update_vtex_account(uuid4(), {"vtex_account": "xyz"})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@override_settings(JWT_SECRET_KEY=JWT_PRIVATE_KEY_PEM)
@override_settings(JWT_PUBLIC_KEY=JWT_PUBLIC_KEY_PEM)
class TestUpdateProjectVTEXAccountViewWithJWTAuthentication(
    BaseTestUpdateProjectVTEXAccountView
):
    def setUp(self):
        self.project = Project.objects.create(name="Alphabet", vtex_account="abc")
        token = JWTService().generate_jwt_token(self.project.uuid)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_can_update_vtex_account_with_jwt_authentication(self):
        with self.assertLogs(
            "insights.projects.usecases.update_vtex_account", level="INFO"
        ) as logs:
            response = self.update_vtex_account(
                self.project.uuid, {"vtex_account": "xyz"}
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "project": {
                    "name": self.project.name,
                    "uuid": str(self.project.uuid),
                    "vtex_account": "xyz",
                }
            },
        )

        self.project.refresh_from_db()
        self.assertEqual(self.project.vtex_account, "xyz")

        expected_message = (
            f"[UpdateProjectVTEXAccount] VTEX Account for project "
            f"{self.project.name} ({self.project.uuid}) changed from "
            f"'abc' to 'xyz' by INTERNAL"
        )
        self.assertIn(expected_message, logs.output[0])

    def test_cannot_update_vtex_account_with_invalid_jwt_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")

        response = self.update_vtex_account(self.project.uuid, {"vtex_account": "xyz"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_update_vtex_account_with_invalid_body_via_jwt(self):
        response = self.update_vtex_account(self.project.uuid, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["vtex_account"][0].code, "required")

    def test_cannot_update_vtex_account_when_project_does_not_exist_via_jwt(self):
        response = self.update_vtex_account(uuid4(), {"vtex_account": "xyz"})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
