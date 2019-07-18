from django.urls import path

from .views import (
    ReviewCreateOrUpdateView,
    ReviewDeleteView,
    ReviewDetailView,
    ReviewListView,
)

app_name = 'reviews'

urlpatterns = [
    path('reviews/', ReviewListView.as_view(), name='list'),
    path('reviews/<int:pk>/', ReviewDetailView.as_view(), name="review"),
    path('reviews/<int:pk>/delete/', ReviewDeleteView.as_view(), name="delete"),
    path('review/', ReviewCreateOrUpdateView.as_view(), name='form'),
]
