from django.urls import path

from .views import MailchimpSubscribeView


app_name = 'newsletter'


urlpatterns = [
    path('subscribe/', MailchimpSubscribeView.as_view(), name='subscribe')
]
