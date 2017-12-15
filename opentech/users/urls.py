from django.conf.urls import url

from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^$', auth_views.login, {
        'template_name': 'users/login.html'
    }, name='login'),
    url(r'^login$', auth_views.login, {
        'template_name': 'users/login.html'
    }, name='login'),

    # Log out
    url(r'^logout/$', auth_views.logout, {'next_page': '/'}, name='logout'),
]
