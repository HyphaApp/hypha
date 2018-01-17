from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.urls import reverse_lazy

from wagtail.wagtailadmin.views.account import password_management_enabled

from .decorators import require_oauth_whitelist


@login_required(login_url=reverse_lazy('users:login'))
def account(request):
    "Account page placeholder view"

    return render(request, 'users/account.html', {
        'show_change_password': password_management_enabled() and request.user.has_usable_password(),
    })


@login_required(login_url=reverse_lazy('users:login'))
@require_oauth_whitelist
def oauth(request):
    """
    Generic, empty view for the OAuth associations.
    """

    return TemplateResponse(request, 'users/oauth.html', {})
