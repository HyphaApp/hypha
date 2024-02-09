from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import include, path, reverse_lazy
from django.views.generic import RedirectView
from django_ratelimit.decorators import ratelimit
from elevate.views import elevate as elevate_view

from .views import (
    AccountView,
    ActivationView,
    BackupTokensView,
    EmailChangeConfirmationView,
    EmailChangeDoneView,
    LoginView,
    PasswordLessLoginSignupView,
    PasswordlessLoginView,
    PasswordlessSignupView,
    PasswordResetConfirmView,
    PasswordResetView,
    RegisterView,
    RegistrationSuccessView,
    TWOFAAdminDisableView,
    TWOFADisableView,
    TWOFASetupView,
    account_email_change,
    create_password,
    elevate_check_code_view,
    oauth,
    send_confirm_access_email_view,
    set_password_view,
)

app_name = "users"


public_urlpatterns = [
    path(
        "auth/", PasswordLessLoginSignupView.as_view(), name="passwordless_login_signup"
    ),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path(
        "register-success/", RegistrationSuccessView.as_view(), name="register-success"
    ),
]

account_urls = [
    path(
        "",
        ratelimit(key="ip", rate=settings.DEFAULT_RATE_LIMIT, method="GET")(
            AccountView.as_view()
        ),
        name="account",
    ),
    path(
        "change-email/",
        account_email_change,
        name="email_change_confirm_password",
    ),
    path(
        "password/",
        include(
            [
                path(
                    "change/",
                    ratelimit(
                        key="user",
                        rate=settings.DEFAULT_RATE_LIMIT,
                        method="POST",
                    )(
                        auth_views.PasswordChangeView.as_view(
                            template_name="users/change_password.html",
                            success_url=reverse_lazy("users:account"),
                        )
                    ),
                    name="password_change",
                ),
                path(
                    "reset/",
                    PasswordResetView.as_view(),
                    name="password_reset",
                ),
                path(
                    "reset/done/",
                    auth_views.PasswordResetDoneView.as_view(
                        template_name="users/password_reset/done.html"
                    ),
                    name="password_reset_done",
                ),
                path(
                    "reset/confirm/<uidb64>/<token>/",
                    PasswordResetConfirmView.as_view(),
                    name="password_reset_confirm",
                ),
                path(
                    "reset/complete/",
                    auth_views.PasswordResetCompleteView.as_view(
                        template_name="users/password_reset/complete.html"
                    ),
                    name="password_reset_complete",
                ),
            ]
        ),
    ),
    path(
        "confirmation/done/",
        EmailChangeDoneView.as_view(),
        name="confirm_link_sent",
    ),
    path(
        "confirmation/<uidb64>/<token>/",
        EmailChangeConfirmationView.as_view(),
        name="confirm_email",
    ),
    path(
        "activate/<uidb64>/<token>/",
        ActivationView.as_view(),
        name="activate",
    ),
    path("activate/", create_password, name="activate_password"),
    path("oauth", oauth, name="oauth"),
    # 2FA
    path("two_factor/setup/", TWOFASetupView.as_view(), name="setup"),
    path(
        "two_factor/backup_tokens/",
        BackupTokensView.as_view(),
        name="backup_tokens",
    ),
    path("two_factor/disable/", TWOFADisableView.as_view(), name="disable"),
    path(
        "two_factor/admin/disable/<str:user_id>/",
        TWOFAAdminDisableView.as_view(),
        name="admin_disable",
    ),
    path(
        "auth/<uidb64>/<token>/signup/",
        PasswordlessSignupView.as_view(),
        name="do_passwordless_signup",
    ),
    path(
        "auth/<uidb64>/<token>/",
        PasswordlessLoginView.as_view(),
        name="do_passwordless_login",
    ),
    path(
        "auth/set-user-password/",
        set_password_view,
        name="set_user_password",
    ),
    path(
        "sessions/trusted-device/",
        elevate_view,
        {"template_name": "elevate/elevate.html"},
        name="elevate",
    ),
    path(
        "sessions/send-confirm-access-email/",
        send_confirm_access_email_view,
        name="elevate_send_confirm_access_email",
    ),
    path(
        "sessions/verify-confirmation-code/",
        elevate_check_code_view,
        name="elevate_check_code",
    ),
]

urlpatterns = public_urlpatterns + [
    path("account/", include(account_urls)),
    # this must be above two factor include, this skip displaying the success
    # page and advances user to download backup code page.
    path(
        "account/two_factor/setup/complete/",
        RedirectView.as_view(url=reverse_lazy("users:backup_tokens"), permanent=False),
        name="two_factor:setup_complete",
    ),
]
