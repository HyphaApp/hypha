from rest_framework import pagination


class StandardResultsSetPagination(pagination.PageNumberPagination):
    page_size_query_param = 'page_size'
    max_page_size = 1000
