"""
Storage configuration

This controls where the media on the sites is stored.

DEFAULT_FILE_STORAGE
This is the standard Django storage setting, this is intended
to store all data that is not sensitive to applicants

PRIVATE_FILE_STORAGE
This is the app specific storage setting that allows you to define a different
storage location for all media that is associated with applications and
projects. It should be a path to a storage class the same way that
DEFAULT_FILE_STORAGE is configured

WARNING: If you do not set the PRIVATE_FILE_STORAGE, then applicant media will
be stored in the DEFAULT_FILE_STORAGE. This may be acceptable if the correct
access permissions exist to prevent access to the sub-directory of applicant
media.
"""
DEFAULT_FILE_STORAGE = 'path.to.my.StorageClass'
PRIVATE_FILE_STORAGE = 'path.to.my.PrivateStorageClass'
