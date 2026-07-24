from unittest.mock import MagicMock

from django.test import TestCase

from insights.dashboards.models import Dashboard
from insights.metrics.meta.models import (
    FAVORITE_TEMPLATE_LIMIT_PER_DASHBOARD,
    FavoriteTemplate,
)
from insights.metrics.meta.usecases.move_favorite_templates import (
    MoveFavoriteTemplatesUseCase,
)
from insights.projects.models import Project


class TestMoveFavoriteTemplatesUseCase(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.old_dashboard = Dashboard.objects.create(
            project=self.project,
            name="Old Meta dashboard",
            config={
                "is_whatsapp_integration": True,
                "waba_id": "old_waba",
            },
        )
        self.new_dashboard = Dashboard.objects.create(
            project=self.project,
            name="New Meta dashboard",
            config={
                "is_whatsapp_integration": True,
                "waba_id": "new_waba",
            },
        )
        self.meta_client = MagicMock()
        self.usecase = MoveFavoriteTemplatesUseCase(meta_client=self.meta_client)

    def test_moves_favorites_resolving_template_ids_by_exact_name(self):
        FavoriteTemplate.objects.create(
            dashboard=self.old_dashboard,
            template_id="old-template-1",
            name="promo_cart",
        )
        FavoriteTemplate.objects.create(
            dashboard=self.old_dashboard,
            template_id="old-template-2",
            name="order_status",
        )
        self.meta_client.get_templates_list.side_effect = [
            {
                "data": [
                    {"id": "similar", "name": "promo_cart_v2"},
                    {"id": "new-template-1", "name": "promo_cart"},
                ]
            },
            {"data": [{"id": "new-template-2", "name": "order_status"}]},
        ]

        moved = self.usecase.execute(
            old_dashboard_uuid=self.old_dashboard.uuid,
            new_dashboard_uuid=self.new_dashboard.uuid,
        )

        self.assertEqual(moved, 2)
        favorites = FavoriteTemplate.objects.filter(dashboard=self.new_dashboard)
        self.assertEqual(favorites.count(), 2)
        self.assertTrue(
            favorites.filter(template_id="new-template-1", name="promo_cart").exists()
        )
        self.assertTrue(
            favorites.filter(
                template_id="new-template-2", name="order_status"
            ).exists()
        )
        self.assertEqual(
            FavoriteTemplate.objects.filter(dashboard=self.old_dashboard).count(),
            2,
        )

    def test_skips_favorite_when_template_name_is_missing_on_new_waba(self):
        FavoriteTemplate.objects.create(
            dashboard=self.old_dashboard,
            template_id="old-template-1",
            name="brand_new_template",
        )
        self.meta_client.get_templates_list.return_value = {"data": []}

        moved = self.usecase.execute(
            old_dashboard_uuid=self.old_dashboard.uuid,
            new_dashboard_uuid=self.new_dashboard.uuid,
        )

        self.assertEqual(moved, 0)
        self.assertFalse(
            FavoriteTemplate.objects.filter(dashboard=self.new_dashboard).exists()
        )

    def test_does_not_duplicate_existing_favorites_on_new_dashboard(self):
        FavoriteTemplate.objects.create(
            dashboard=self.old_dashboard,
            template_id="old-template-1",
            name="promo_cart",
        )
        FavoriteTemplate.objects.create(
            dashboard=self.new_dashboard,
            template_id="new-template-1",
            name="promo_cart",
        )
        self.meta_client.get_templates_list.return_value = {
            "data": [{"id": "new-template-1", "name": "promo_cart"}]
        }

        moved = self.usecase.execute(
            old_dashboard_uuid=self.old_dashboard.uuid,
            new_dashboard_uuid=self.new_dashboard.uuid,
        )

        self.assertEqual(moved, 0)
        self.assertEqual(
            FavoriteTemplate.objects.filter(dashboard=self.new_dashboard).count(),
            1,
        )

    def test_stops_when_favorite_limit_is_reached(self):
        for index in range(FAVORITE_TEMPLATE_LIMIT_PER_DASHBOARD):
            FavoriteTemplate.objects.create(
                dashboard=self.new_dashboard,
                template_id=f"existing-{index}",
                name=f"existing_{index}",
            )
        FavoriteTemplate.objects.create(
            dashboard=self.old_dashboard,
            template_id="old-template-1",
            name="promo_cart",
        )

        moved = self.usecase.execute(
            old_dashboard_uuid=self.old_dashboard.uuid,
            new_dashboard_uuid=self.new_dashboard.uuid,
        )

        self.assertEqual(moved, 0)
        self.meta_client.get_templates_list.assert_not_called()

    def test_reads_favorites_from_soft_deleted_old_dashboard(self):
        FavoriteTemplate.objects.create(
            dashboard=self.old_dashboard,
            template_id="old-template-1",
            name="promo_cart",
        )
        self.old_dashboard.delete()
        self.meta_client.get_templates_list.return_value = {
            "data": [{"id": "new-template-1", "name": "promo_cart"}]
        }

        moved = self.usecase.execute(
            old_dashboard_uuid=self.old_dashboard.uuid,
            new_dashboard_uuid=self.new_dashboard.uuid,
        )

        self.assertEqual(moved, 1)
        self.assertTrue(
            FavoriteTemplate.objects.filter(
                dashboard=self.new_dashboard,
                template_id="new-template-1",
            ).exists()
        )
