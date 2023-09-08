from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import include, path, reverse_lazy
from django_ratelimit.decorators import ratelimit

from .views import (
    AccountView,
    ActivationView,
    EmailChangeConfirmationView,
    EmailChangeDoneView,
    EmailChangePasswordView,
    LoginView,
    PasswordResetConfirmView,
    PasswordResetView,
    RegisterView,
    RegistrationSuccessView,
    TWOFAAdminDisableView,
    TWOFABackupTokensPasswordView,
    TWOFADisableView,
    TWOFARequiredMessageView,
    TWOFASetupView,
    become,
    create_password,
    oauth,
)

app_name = "users"


public_urlpatterns = [
    path(
        "login/",
        LoginView.as_view(
            template_name="users/login.html", redirect_authenticated_user=True
        ),
        name="login",
    ),
    # Log out
    path("logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path(
        "register-success/", RegistrationSuccessView.as_view(), name="register-success"
    ),
]

urlpatterns = [
    path(
        "account/",
        include(
            [
                path(
                    "",
                    ratelimit(key="ip", rate=settings.DEFAULT_RATE_LIMIT, method="GET")(
                        AccountView.as_view()
                    ),
                    name="account",
                ),
                path(
                    "password/",
                    include(
                        [
                            path(
                                "",
                                EmailChangePasswordView.as_view(),
                                name="email_change_confirm_password",
                            ),
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
                # Two factor redirect
                path(
                    "two_factor/required/",
                    TWOFARequiredMessageView.as_view(),
                    name="two_factor_required",
                ),
                path("two_factor/setup/", TWOFASetupView.as_view(), name="setup"),
                path(
                    "two_factor/backup_tokens/password/",
                    TWOFABackupTokensPasswordView.as_view(),
                    name="backup_tokens_password",
                ),
                path("two_factor/disable/", TWOFADisableView.as_view(), name="disable"),
                path(
                    "two_factor/admin/disable/<str:user_id>/",
                    TWOFAAdminDisableView.as_view(),
                    name="admin_disable",
                ),
            ]
        ),
    ),
]

if settings.HIJACK_ENABLE:
    urlpatterns += [
        path("account/become/", become, name="become"),
    ]
