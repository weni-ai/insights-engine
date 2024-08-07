# Generated by Django 5.0.4 on 2024-07-24 17:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboards", "0003_remove_dashboard_unique_true_default_dashboard_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="dashboard",
            name="is_deletable",
            field=models.BooleanField(default=False, verbose_name="Is detetable?"),
        ),
        migrations.AddField(
            model_name="dashboard",
            name="is_editable",
            field=models.BooleanField(default=False, verbose_name="Is editable?"),
        ),
    ]
