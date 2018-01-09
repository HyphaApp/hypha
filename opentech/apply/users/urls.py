from django.conf.urls import url

from django.contrib.auth import views as auth_views

from django.urls import reverse_lazy

from wagtail.wagtailadmin.forms import PasswordResetForm

from opentech.users.views import account

urlpatterns = [
    url(r'^$', account, name='account'),
    url(
        r'^login/$',
        auth_views.LoginView.as_view(
            template_name='users/login.html',
            redirect_authenticated_user=True
        ),
        name='login'
    ),

    # Log out
    url(r'^logout/$', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    # Password reset
    url(r'^reset/$', auth_views.PasswordResetView.as_view(
        template_name='users/password_reset/form.html',
        email_template_name='users/password_reset/email.txt',
        success_url=reverse_lazy('users:password_reset_done'),
        form_class=PasswordResetForm
    )),
    url(
        r'^reset/done/$',
        auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset/done.html'),
        name='password_reset_done'
    ),
    url(
        r'^reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='users/password_reset/confirm.html',
            post_reset_login=True,
            success_url=reverse_lazy('users:account')
        ),
        name='password_reset_confirm'
    ),
    url(
        r'^reset/complete/$',
        auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset/complete.html'),
        name='password_reset_complete'
    ),
]
