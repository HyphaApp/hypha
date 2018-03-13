from django.urls import path

from .esi import views as esi_views
from .search import views as search_views

urlpatterns = [
    path('esi/<slug>/', esi_views.esi, name='esi'),
    path('search/', search_views.search, name='search'),
]
