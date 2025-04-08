from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.response import Response

from insights.authentication.tests.decorators import with_internal_auth
from insights.users.models import User


class BaseTestChangeUserLanguageView(APITestCase):
    def change_user_language(self, data: dict) -> Response:
        url = "/v1/internal/users/change-language/"

        return self.client.post(url, data, format="json")


class TestChangeUserLanguageViewAsAnonymousUser(BaseTestChangeUserLanguageView):
    def test_cannot_change_user_language_when_user_is_anonymous(self):
        response = self.change_user_language(
            {"email": "test@test.com", "language": "en"}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestChangeUserLanguageViewAsAuthenticatedUser(BaseTestChangeUserLanguageView):
    def setUp(self):
        self.user = User.objects.create(email="test@test.com", language="en-us")
        self.client.force_authenticate(user=self.user)

    def test_cannot_change_user_language_when_user_is_not_internal(self):
        response = self.change_user_language(
            {"email": "test@test.com", "language": "pt-br"}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_internal_auth
    def test_change_user_language(self):
        new_language = "pt-br"

        response = self.change_user_language(
            {"email": "test@test.com", "language": new_language}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db(fields=["language"])

        self.assertEqual(self.user.language, new_language)

    @with_internal_auth
    def test_cannot_change_language_when_user_does_not_exist(self):
        response = self.change_user_language(
            {"email": "non-existent@test.com", "language": "pt-br"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["email"][0].code,
            "does_not_exist",
        )
