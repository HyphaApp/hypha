from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import storages as get_storage_class
from django.http import FileResponse
from django.views.generic import View

if "private_media_storage" in settings.STORAGES:
    PrivateStorage = get_storage_class["private_media_storage"].__class__
else:
    PrivateStorage = get_storage_class["default"].__class__


class PrivateMediaView(LoginRequiredMixin, View):
    """
    Base view to configure the access to private media stored in the private
    storage location.

    Classes inheriting from this should implement their own access requirements
    based on the file being served, this class will only ensure that the file
    is not made public to unauthenticated users.
    """

    storage = PrivateStorage()

    def get_media(self, *args, **kwargs):
        """
        Convert the URL request to a path and then return the file object

        e.g.
        storage_location = get_my_storage_location(request, **args, **kwargs)
        return self.storage.open(storage_location)
        """
        raise NotImplementedError()

    def get(self, *args, **kwargs):
        file_to_serve = self.get_media(*args, **kwargs)
        return FileResponse(file_to_serve)
