from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class PublicMediaStorage(S3Boto3Storage):
    bucket_name = settings.AWS_PUBLIC_BUCKET_NAME
    file_overwrite = False
    querystring_auth = False
    url_protocol = 'https:'


class PrivateMediaStorage(S3Boto3Storage):
    bucket_acl = 'private'
    bucket_name = settings.AWS_PRIVATE_BUCKET_NAME
    custom_domain = False
    default_acl = 'private'
    encryption = True
    file_overwrite = False
    querystring_auth = True
    url_protocol = 'https:'
