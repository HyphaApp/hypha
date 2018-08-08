from django.contrib import messages
from django.contrib.auth import get_user_model, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.shortcuts import redirect, render
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.views.generic import UpdateView
from django.views.generic.base import TemplateView

from hijack.views import login_with_id

from wagtail.admin.views.account import password_management_enabled

from .decorators import require_oauth_whitelist
from .forms import ProfileForm


User = get_user_model()


@method_decorator(login_required, name='dispatch')
class AccountView(UpdateView):
    form_class = ProfileForm
    template_name = 'users/account.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self,):
        return reverse_lazy('users:account')

    def get_context_data(self, **kwargs):
        if self.request.user.is_superuser:
            swappable = User.objects.filter(is_active=True, is_superuser=False)
        else:
            swappable = []

        show_change_password = password_management_enabled() and self.request.user.has_usable_password(),

        return super().get_context_data(
            swappable=swappable,
            show_change_password=show_change_password,
            **kwargs,
        )


@login_required()
def become(request):
    if request.POST:
        id = request.POST['user']
        return login_with_id(request, id)
    return redirect('users:account')


@login_required()
@require_oauth_whitelist
def oauth(request):
    """Generic, empty view for the OAuth associations."""

    return TemplateResponse(request, 'users/oauth.html', {})


class ActivationView(TemplateView):
    def get(self, request, *args, **kwargs):
        user = self.get_user(kwargs.get('uidb64'))

        if self.valid(user, kwargs.get('token')):
            user.is_active = True
            user.save()

            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            return redirect('users:activate_password')

        return render(request, 'users/activation/invalid.html')

    def valid(self, user, token):
        """
        Verify that the activation token is valid and within the
        permitted activation time window.
        """

        token_generator = PasswordResetTokenGenerator()
        return user is not None and token_generator.check_token(user, token)

    def get_user(self, uidb64):
        """
        Given the verified uid, look up and return the
        corresponding user account if it exists, or ``None`` if it
        doesn't.
        """
        try:
            user = User.objects.get(**{
                'pk': force_text(urlsafe_base64_decode(uidb64)),
                'is_active': False
            })
            return user
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None


def create_password(request):
    """
    A custom view for the admin password change form used for account activation.
    """

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
