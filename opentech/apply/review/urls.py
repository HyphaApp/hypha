from django.urls import path

from .views import ReviewDetailView, ReviewListView, ReviewCreateOrUpdateView

app_name = 'reviews'

urlpatterns = [
    path('reviews/', ReviewListView.as_view(), name='list'),
    path('reviews/<int:pk>/', ReviewDetailView.as_view(), name="review"),
    path('review/', ReviewCreateOrUpdateView.as_view(), name='form'),
]
