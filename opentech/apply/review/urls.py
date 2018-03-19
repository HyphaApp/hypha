from django.urls import path

from .views import CreateReviewView


app_name = 'reviews'

urlpatterns = [
    path('', CreateReviewView.as_view(), name='create'),
]
