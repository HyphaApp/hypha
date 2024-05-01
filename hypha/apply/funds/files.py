import os

from django.urls import reverse

from hypha.apply.stream_forms.files import StreamFieldFile


def generate_private_file_path(entity_id, field_id, file_name, path_start="submission"):
    path = os.path.join(path_start, str(entity_id), str(field_id))
    if file_name.startswith(path):
        return file_name

    return os.path.join(path, file_name)


class PrivateStreamFieldFile(StreamFieldFile):
    """
    Represents a file from a Wagtail/Hypha Stream Form block.
    Aside: with imports in their usual place, there could be circular imports. Deferring or delaying import to methods
    resolves the issue.
    """

    def get_entity_id(self):
        from hypha.apply.funds.models import ApplicationRevision
        from hypha.apply.projects.models import ReportVersion

        entity_id = self.instance.pk

        if isinstance(self.instance, ApplicationRevision):
            entity_id = self.instance.submission.pk
        elif isinstance(self.instance, ReportVersion):
            # Reports are project documents.
            entity_id = self.instance.report.project.pk
        return entity_id

    def generate_filename(self):
        from hypha.apply.projects.models import ReportVersion

        path_start = "submission"
        if isinstance(self.instance, ReportVersion):
            path_start = "project"
        return generate_private_file_path(
            self.get_entity_id(),
            self.field.id,
            self.name,
            path_start=path_start,
        )

    @property
    def url(self):
        from hypha.apply.projects.models import ReportVersion

        view_name = "apply:submissions:serve_private_media"
        kwargs = {
            "pk": self.get_entity_id(),
            "field_id": self.field.id,
            "file_name": self.basename,
        }
        if isinstance(self.instance, ReportVersion):
            view_name = "apply:projects:document"
        return reverse(viewname=view_name, kwargs=kwargs)
