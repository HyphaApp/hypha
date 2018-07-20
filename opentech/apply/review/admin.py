from wagtail.contrib.modeladmin.options import ModelAdmin

from opentech.apply.review.models import ReviewForm


class ReviewFormAdmin(ModelAdmin):
    model = ReviewForm
    menu_icon = 'form'
