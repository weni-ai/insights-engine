# Generated by Django 5.0.4 on 2024-06-06 17:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("widgets", "0002_remove_widget_report_report"),
    ]

    operations = [
        migrations.RenameField(
            model_name="report",
            old_name="w_type",
            new_name="type",
        ),
        migrations.RenameField(
            model_name="widget",
            old_name="w_type",
            new_name="type",
        ),
    ]