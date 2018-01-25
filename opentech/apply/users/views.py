from django.contrib import messages
from django.contrib.auth import get_user_model, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.shortcuts import redirect, render
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.views.generic.base import TemplateView

from wagtail.wagtailadmin.views.account import password_management_enabled

from .decorators import require_oauth_whitelist


@login_required(login_url=reverse_lazy('users:login'))
def account(request):
    """Account page placeholder view"""

    return render(request, 'users/account.html', {
        'show_change_password': password_management_enabled() and request.user.has_usable_password(),
    })


@login_required(login_url=reverse_lazy('users:login'))
@require_oauth_whitelist
def oauth(request):
    """Generic, empty view for the OAuth associations."""

    return TemplateResponse(request, 'users/oauth.html', {})


class ActivationView(TemplateView):
    """
    Inspired by https://github.com/ubernostrum/django-registration
    """

    def get(self, request, *args, **kwargs):
        user = self.activate(*args, **kwargs)
        if user:
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            return redirect('users:activate_password')

        return render(request, 'users/activation/invalid.html')

    def activate(self, *args, **kwargs):
        user = self.validate_token(kwargs.get('uidb64'), kwargs.get('token'))
        if user:
            user.is_active = True
            user.save()
            return user
        return False

    def validate_token(self, uidb64, token):
        """
        Verify that the activation key is valid and within the
        permitted activation time window, returning the username if
        valid or ``None`` if not.
        """

        uid = force_text(urlsafe_base64_decode(uidb64))
        user = self.get_user(uid)
        token_generator = PasswordResetTokenGenerator()

        if user is not None and token_generator.check_token(user, token):
            return user

        return False

    def get_user(self, uid):
        """
        Given the verified uid, look up and return the
        corresponding user account if it exists, or ``None`` if it
        doesn't.
        """
        User = get_user_model()

        try:
            user = User.objects.get(**{
                'pk': uid,
                'is_active': False
            })
            return user
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None


def create_password(request):
    if request.method == 'POST':
        form = AdminPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('users:account')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminPasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {
        'form': form
    })
