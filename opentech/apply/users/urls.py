from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

from opentech.apply.users.views import account, oauth, ActivationView, create_password

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

    # Password change
    url(
        r'^password/$',
        auth_views.PasswordChangeView.as_view(
            template_name="users/change_password.html",
            success_url=reverse_lazy('users:account')
        ),
        name='password_change',
    ),

    # Password reset
    url(r'^reset/$', auth_views.PasswordResetView.as_view(
        template_name='users/password_reset/form.html',
        email_template_name='users/password_reset/email.txt',
        success_url=reverse_lazy('users:password_reset_done')
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
            post_reset_login_backend='django.contrib.auth.backends.ModelBackend',
            success_url=reverse_lazy('users:account')
        ),
        name='password_reset_confirm'
    ),
    url(
        r'^reset/complete/$',
        auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset/complete.html'),
        name='password_reset_complete'
    ),
    url(
        r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        ActivationView.as_view(),
        name='activate'
    ),
    url(r'^activate/password/', create_password, name="activate_password"),
    url(r'^oauth$', oauth, name='oauth'),
]
