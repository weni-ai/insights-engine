from insights.projects.models import Project


def enable_custom_dashboard(project: Project):
    project.config["allowed_project"] = True
    project.save()
