from django.conf.urls import url

from django.contrib.auth import views as auth_views

urlpatterns = [
    # TODO replace with dashboard view with a login_required decorator
    url(r'^$', auth_views.login, {
        'template_name': 'users/login.html'
    }, name='user'),
    url(r'^login$', auth_views.login, {
        'template_name': 'users/login.html'
    }, name='login'),

    # Log out
    url(r'^logout/$', auth_views.logout, {'next_page': '/'}, name='logout'),
]
