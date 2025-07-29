from uuid import UUID
import uuid
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework.response import Response
from rest_framework import status


class BaseTestWidgetViewSet(APITestCase):
    def create_widget(self, data: dict) -> Response:
        url = reverse("widget-list")

        return self.client.post(url, data)

    def list_widgets(self) -> Response:
        url = reverse("widget-list")

        return self.client.get(url)

    def update_widget(self, widget_uuid: UUID, data: dict) -> Response:
        url = reverse("widget-detail", args=[widget_uuid])

        return self.client.patch(url, data)

    def delete_widget(self, widget_uuid: UUID) -> Response:
        url = reverse("widget-detail", args=[widget_uuid])

        return self.client.delete(url)


class TestWidgetViewSetAsAnonymousUser(BaseTestWidgetViewSet):
    def test_list_widgets(self) -> None:
        response = self.list_widgets()

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_widget(self) -> None:
        response = self.create_widget({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_widget(self) -> None:
        response = self.update_widget(uuid.uuid4(), {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_widget(self) -> None:
        response = self.delete_widget(uuid.uuid4())

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
