from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from wagtail.wagtailadmin.views.account import password_management_enabled


@login_required(login_url='/user/login')
def account(request):
    "Account page placeholder view"

    return render(request, 'users/account.html', {
        'show_change_password': password_management_enabled() and request.user.has_usable_password(),
    })
