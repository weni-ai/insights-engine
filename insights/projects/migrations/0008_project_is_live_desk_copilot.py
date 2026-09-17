from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0007_set_multi_agents_for_projects_with_conversations_dashboard"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="is_live_desk_copilot",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="project",
            name="parent_project_uuid",
            field=models.UUIDField(blank=True, null=True),
        ),
    ]
