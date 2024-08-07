# Generated by Django 5.0.3 on 2024-04-01 17:54

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("dashboards", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Widget",
            fields=[
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4, primary_key=True, serialize=False
                    ),
                ),
                (
                    "created_on",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created on"),
                ),
                (
                    "modified_on",
                    models.DateTimeField(auto_now=True, verbose_name="Modified on"),
                ),
                (
                    "name",
                    models.CharField(default=None, max_length=255, verbose_name="Name"),
                ),
                (
                    "w_type",
                    models.CharField(
                        default=None, max_length=50, verbose_name="Widget Type"
                    ),
                ),
                (
                    "source",
                    models.CharField(
                        default=None, max_length=50, verbose_name="Data Source"
                    ),
                ),
                ("position", models.JSONField(verbose_name="Widget position")),
                ("config", models.JSONField(verbose_name="Widget Configuration")),
                ("report", models.JSONField(verbose_name="Widget Report")),
                (
                    "dashboard",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="widgets",
                        to="dashboards.dashboard",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
