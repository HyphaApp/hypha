import mimetypes
from wsgiref.util import FileWrapper

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.files.storage import get_storage_class
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View

from opentech.apply.funds.permissions import is_user_has_access_to_view_submission


private_file_storage = getattr(settings, 'PRIVATE_FILE_STORAGE', None)
private_storage = get_storage_class(private_file_storage)


class PrivateMediaView(UserPassesTestMixin, View):

    def get(self, *args, **kwargs):
        # TODo: make this work for other classes with private files
        submission_id = kwargs['pk']
        field_id = kwargs['field_id']
        file_name = kwargs['file_name']
        file_name_with_path = f'submission/{submission_id}/{field_id}/{file_name}'

        file_to_serve = private_storage().open(file_name_with_path)
        wrapper = FileWrapper(file_to_serve)
        encoding_map = {
            'bzip2': 'application/x-bzip',
            'gzip': 'application/gzip',
            'xz': 'application/x-xz',
        }
        content_type, encoding = mimetypes.guess_type(file_name)
        # Encoding isn't set to prevent browsers from automatically uncompressing files.
        content_type = encoding_map.get(encoding, content_type)
        content_type = content_type or 'application/octet-stream'
        # From Django 2.1, we can use FileResponse instead of StreamingHttpResponse
        response = StreamingHttpResponse(wrapper, content_type=content_type)

        response['Content-Disposition'] = f'filename={file_name}'
        response['Content-Length'] = submission_file.size

        return response

    def test_func(self):
        submission_id = self.kwargs['pk']
        submission = get_object_or_404(ApplicationSubmission, id=submission_id)

        return is_user_has_access_to_view_submission(self.request.user, submission)

    def handle_no_permission(self):
        # This method can be removed after upgrading Django to 2.1
        # https://github.com/django/django/commit/9b1125bfc7e2dc747128e6e7e8a2259ff1a7d39f
        # In older versions, authenticated users who lacked permissions were
        # redirected to the login page (which resulted in a loop) instead of
        # receiving an HTTP 403 Forbidden response.
        if self.raise_exception or self.request.user.is_authenticated:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect_to_login(self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())
