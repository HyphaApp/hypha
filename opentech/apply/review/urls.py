from django.urls import path

from .views import ReviewCreateView, ReviewDetailView, ReviewListView, ReviewDraftEditView

app_name = 'reviews'

urlpatterns = [
    path('', ReviewListView.as_view(), name='list'),
    path('create', ReviewCreateView.as_view(), name='create'),
    path('<int:pk>', ReviewDetailView.as_view(), name="review"),
    path('<int:pk>/draft', ReviewDraftEditView.as_view(), name='draft'),
]
