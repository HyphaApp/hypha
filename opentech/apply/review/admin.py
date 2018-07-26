from django.conf.urls import url

from wagtail.contrib.modeladmin.options import ModelAdmin
from wagtail.contrib.modeladmin.views import CreateView, InstanceSpecificView

from opentech.apply.review.models import ReviewForm

from .admin_helpers import ButtonsWithClone


class CloneView(CreateView, InstanceSpecificView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.pk = None


class ReviewFormAdmin(ModelAdmin):
    model = ReviewForm
    menu_icon = 'form'
    button_helper_class = ButtonsWithClone
    clone_view_class = CloneView

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
