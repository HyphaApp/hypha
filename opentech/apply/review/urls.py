from django.urls import path

from .views import ReviewCreateView, ReviewListView


app_name = 'reviews'

urlpatterns = [
    path('', ReviewListView.as_view(), name='list'),
    path('create', ReviewCreateView.as_view(), name='create'),
]
