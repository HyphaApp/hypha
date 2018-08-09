from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

from opentech.apply.users.views import AccountView, become, oauth, ActivationView, create_password


app_name = 'users'


public_urlpatterns = [
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='users/login.html',
            redirect_authenticated_user=True
        ),
        name='login'
    ),

    # Log out
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]


urlpatterns = [
    path('account/', include([
        path('', AccountView.as_view(), name='account'),
        path('become/', become, name='become'),
        path('password/', include([
            path(
                'change/',
                auth_views.PasswordChangeView.as_view(
                    template_name="users/change_password.html",
                    success_url=reverse_lazy('users:account')
                ),
                name='password_change',
            ),
            path(
                'reset/',
                auth_views.PasswordResetView.as_view(
                    template_name='users/password_reset/form.html',
                    email_template_name='users/password_reset/email.txt',
                    success_url=reverse_lazy('users:password_reset_done')
                ),
                name='password_reset',
            ),
            path(
                'reset/done/',
                auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset/done.html'),
                name='password_reset_done'
            ),
            path(
                'reset/confirm/<uidb64>/<token>/',
                auth_views.PasswordResetConfirmView.as_view(
                    template_name='users/password_reset/confirm.html',
                    post_reset_login=True,
                    post_reset_login_backend='django.contrib.auth.backends.ModelBackend',
                    success_url=reverse_lazy('users:account')
                ),
                name='password_reset_confirm'
            ),
            path(
                'reset/complete/',
                auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset/complete.html'),
                name='password_reset_complete'
            ),
        ])),
        path(
            'activate/<uidb64>/<token>/',
            ActivationView.as_view(),
            name='activate'
        ),
        path('activate/', create_password, name="activate_password"),
        path('oauth', oauth, name='oauth'),
    ]))
]
