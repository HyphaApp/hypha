from urllib import parse

from django.conf import settings
from django.utils.encoding import filepath_to_uri
from storages.backends.s3boto3 import S3Boto3Storage


"""
This app defines the storage classes that are used to store the private and
public media in the application. When the app moves to an installable app,
users will be able to implement their own storage backends with different
providers e.g. Azure

Most private files are served through the webapp to allow users to share links
to the file and the recipient is then authenticated through the app rather than
with the original file url with auth string.

Please set the following settings in order to configure this:
DEFAULT_FILE_STORAGE
PRIVATE_FILE_STORAGE
"""


class PublicMediaStorage(S3Boto3Storage):
    if hasattr(settings, 'AWS_PUBLIC_BUCKET_NAME'):
        bucket_name = settings.AWS_PUBLIC_BUCKET_NAME

    if hasattr(settings, 'AWS_PUBLIC_CUSTOM_DOMAIN'):
        custom_domain = settings.AWS_PUBLIC_CUSTOM_DOMAIN

    file_overwrite = False
    querystring_auth = False
    url_protocol = 'https:'


class PrivateMediaStorage(S3Boto3Storage):
    if hasattr(settings, 'AWS_PRIVATE_BUCKET_NAME'):
        bucket_name = settings.AWS_PRIVATE_BUCKET_NAME

    bucket_acl = 'private'
    custom_domain = False
    default_acl = 'private'
    encryption = True
    file_overwrite = False
    querystring_auth = True
    url_protocol = 'https:'

    def url(self, name, parameters=None, expire=None):
        url = super().url(name, parameters, expire)

        if hasattr(settings, 'AWS_PRIVATE_CUSTOM_DOMAIN'):
            # Django storage doesn't handle custom domains with auth strings
            custom_domain = settings.AWS_PRIVATE_CUSTOM_DOMAIN
            parts = list(parse.urlsplit(url))
            parts[1:3] = custom_domain, filepath_to_uri(name)
            return parse.urlunsplit(parts)

        return url
