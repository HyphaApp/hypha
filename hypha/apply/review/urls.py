from django.urls import path

from .views import ReviewDetailView, ReviewListView, ReviewCreateOrUpdateView, ReviewDeleteView, ReviewEditView

app_name = 'reviews'

urlpatterns = [
    path('reviews/', ReviewListView.as_view(), name='list'),
    path('reviews/<int:pk>/', ReviewDetailView.as_view(), name="review"),
    path('reviews/<int:pk>/delete/', ReviewDeleteView.as_view(), name="delete"),
    path('reviews/<int:pk>/edit/', ReviewEditView.as_view(), name="edit"),
    path('review/', ReviewCreateOrUpdateView.as_view(), name='form'),
]
