from urllib import parse

from django.conf import settings
from django.urls import reverse
from django.utils.encoding import filepath_to_uri
from storages.backends.s3boto3 import S3Boto3Storage


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

    def url(self, name, parameters=None, expire=None, proxy_url=True):
        if proxy_url:
            try:
                name_parts = name.split('/')
                # Create and return Proxy URL only for submissions
                if name_parts[0] == 'submission':
                    return reverse(
                        'apply:submissions:private_media_redirect', kwargs={
                            'submission_id': name_parts[1], 'field_id': name_parts[2],
                            'file_name': name_parts[3]
                        }
                    )
            except IndexError:
                pass

        url = super().url(name, parameters, expire)

        if hasattr(settings, 'AWS_PRIVATE_CUSTOM_DOMAIN'):
            # Django storage doesn't handle custom domains with auth strings
            custom_domain = settings.AWS_PRIVATE_CUSTOM_DOMAIN
            parts = list(parse.urlsplit(url))
            parts[1:3] = custom_domain, filepath_to_uri(name)
            return parse.urlunsplit(parts)

        return url
