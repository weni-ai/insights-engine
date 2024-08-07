# Generated by Django 5.0.3 on 2024-04-03 18:54

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Project",
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
                    "config",
                    models.JSONField(blank=True, null=True, verbose_name="config"),
                ),
                ("name", models.CharField(max_length=255)),
                ("is_template", models.BooleanField(default=False)),
                ("timezone", models.CharField(max_length=64, null=True)),
                ("date_format", models.CharField(max_length=64, null=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ProjectAuth",
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
                    "role",
                    models.IntegerField(
                        choices=[(0, "Not Setted"), (1, "Admin")], default=0
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="authorizations",
                        to="projects.project",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="authorizations",
                        to=settings.AUTH_USER_MODEL,
                        to_field="email",
                    ),
                ),
            ],
            options={
                "unique_together": {("user", "project")},
            },
        ),
    ]
