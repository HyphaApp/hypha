from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    name = "hypha.apply.projects"
    label = "application_projects"

    def ready(self):
        import hypha.apply.projects.signals  # noqa: F401
