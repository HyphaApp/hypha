from rest_framework_api_key.permissions import BaseHasAPIKey

from hypha.apply.home.models import ApplyAPIKey
from hypha.public.home.models import PublicAPIKey


class HasApplyAPIKey(BaseHasAPIKey):
    model = ApplyAPIKey


class HasPublicAPIKey(BaseHasAPIKey):
    model = PublicAPIKey
