from django.conf import settings
from django.core.files.storage import get_storage_class
from django.http import FileResponse
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
        return FileResponse(file_to_serve)
