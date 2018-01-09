from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse


@login_required(login_url='/user/login')
def account(request):
    "Account page placeholder view"
    return TemplateResponse(request, 'users/account.html', {})
