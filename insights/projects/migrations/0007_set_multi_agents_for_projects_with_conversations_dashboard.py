from django.db import migrations


def set_multi_agents_for_projects_with_conversations_dashboard(apps, schema_editor):
    Project = apps.get_model("projects", "Project")

    projects = (
        Project.objects.filter(dashboards__name="conversations_dashboard.title")
        .exclude(is_nexus_multi_agents_active=True)
        .values_list("pk", flat=True)
    )

    Project.objects.filter(pk__in=projects).update(is_nexus_multi_agents_active=True)


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0006_project_is_nexus_multi_agents_active"),
    ]

    operations = [
        migrations.RunPython(
            set_multi_agents_for_projects_with_conversations_dashboard
        ),
    ]
