import mimetypes
import os
from wsgiref.util import FileWrapper

from django.conf import settings
from django.core.files.storage import get_storage_class
from django.http import StreamingHttpResponse
from django.views.generic import View


private_file_storage = getattr(settings, 'PRIVATE_FILE_STORAGE', None)
PrivateStorage = get_storage_class(private_file_storage)


class PrivateMediaView(View):
    storage = PrivateStorage()

    def get_media(self, *args, **kwargs):
        # Convert the URL request to a path which the storage can use to find the file
        raise NotImplementedError()

    def get(self, *args, **kwargs):
        file_to_serve = self.get_media(*args, **kwargs)
        wrapper = FileWrapper(file_to_serve)
        encoding_map = {
            'bzip2': 'application/x-bzip',
            'gzip': 'application/gzip',
            'xz': 'application/x-xz',
        }
        file_name = os.path.basename(file_to_serve.name)
        content_type, encoding = mimetypes.guess_type(file_name)
        # Encoding isn't set to prevent browsers from automatically uncompressing files.
        content_type = encoding_map.get(encoding, content_type)
        content_type = content_type or 'application/octet-stream'
        # From Django 2.1, we can use FileResponse instead of StreamingHttpResponse
        response = StreamingHttpResponse(wrapper, content_type=content_type)

        response['Content-Disposition'] = f'filename={file_name}'
        response['Content-Length'] = file_to_serve.size

        return response
