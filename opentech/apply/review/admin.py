from django.conf.urls import url

from wagtail.contrib.modeladmin.options import ModelAdmin
from wagtail.contrib.modeladmin.views import CreateView, InstanceSpecificView

from opentech.apply.review.models import ReviewForm
from opentech.apply.utils.admin import ListRelatedMixin

from .admin_helpers import ButtonsWithClone


class CloneView(CreateView, InstanceSpecificView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.pk = None


class ReviewFormAdmin(ListRelatedMixin, ModelAdmin):
    model = ReviewForm
    menu_icon = 'form'
    list_display = ('name', 'used_by')
    button_helper_class = ButtonsWithClone
    clone_view_class = CloneView

    related_models = [
        ('applicationbasereviewform', 'application'),
        ('roundbasereviewform', 'round'),
        ('labbasereviewform', 'lab'),
    ]

    def get_admin_urls_for_registration(self):
        urls = super().get_admin_urls_for_registration()

        urls += (
            url(
                self.url_helper.get_action_url_pattern('clone'),
                self.clone_view,
                name=self.url_helper.get_action_url_name('clone')
            ),
        )

        return urls

    def clone_view(self, request, **kwargs):
        kwargs.update(**{'model_admin': self})
        view_class = self.clone_view_class
        return view_class.as_view(**kwargs)(request)
