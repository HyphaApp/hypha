from django.http import Http404
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from hypha.apply.funds.models import RoundsAndLabs

from .pagination import StandardResultsSetPagination
from .serializers import (
    OpenRoundLabSerializer,
    RoundLabSerializer,
)


class RoundViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    """ViewSet that can be utilized to see the open rounds & labs within Hypha

    This is a "public" REST API that still requires an API key to function. This API key
    can be created in the django-admin as per the `djangorestframework-api-key` docs:
    https://florimondmanca.github.io/djangorestframework-api-key/guide/#creating-and-managing-api-keys

    Requires a `Authorization: Api-Key <API_KEY>` HTTP Header (assuming
    `API_KEY_CUSTOM_HEADER` hasn't been set) and will only work with the proper action
    appended to the end of the URL. ie: `/api/v1/rounds/open`
    """

    serializer_class = RoundLabSerializer

    pagination_class = StandardResultsSetPagination

    @property
    def queryset():
        return RoundsAndLabs.objects.all()

    def get_serializer_class(self):
        return OpenRoundLabSerializer

    def get_permissions(self):
        if self.action != "open":
            raise Http404

        return [HasAPIKey()]

    @action(methods=["get"], detail=False)
    def open(self, request):
        queryset = RoundsAndLabs.objects.open()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
