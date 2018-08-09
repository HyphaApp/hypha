from django.urls import path

from .search import views as search_views

urlpatterns = [
    path('search/', search_views.search, name='search'),
]
