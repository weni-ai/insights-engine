from django.test import TestCase
from django.db import models

from insights.shared.models import SoftDeletableModel


class TestOnlySoftDeletableModel(SoftDeletableModel):
    """
    A test-only model that won't exist outside these tests.
    This model is used to test the SoftDeletableManager functionality.
    """

    name = models.CharField(max_length=100)

    class Meta:
        app_label = "shared"
        db_table = "test_only_soft_deletable_model"


class SoftDeletableManagerTests(TestCase):
    def setUp(self):
        self.instance = TestOnlySoftDeletableModel.objects.create(name="Example")

    def test_get_queryset_with_include_deleted(self):
        self.assertIn(self.instance, TestOnlySoftDeletableModel.objects.all())
        self.assertIn(self.instance, TestOnlySoftDeletableModel.all_objects.all())

        self.instance.delete()

        self.assertNotIn(self.instance, TestOnlySoftDeletableModel.objects.all())
        self.assertIn(self.instance, TestOnlySoftDeletableModel.all_objects.all())
