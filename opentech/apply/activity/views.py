from django.views.generic.edit import ModelFormMixin

from .forms import CommentForm


class CommentFormViewMixin(ModelFormMixin):
    form_class = CommentForm
