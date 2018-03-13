from django.shortcuts import get_object_or_404
from django.views.generic import CreateView

from opentech.apply.funds.models import ApplicationSubmission
from .models import Review


class CreateReviewView(CreateView):
    model = Review
    fields = ['review']
