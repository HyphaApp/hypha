from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.views import SuccessURLAllowedHostsMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render, resolve_url
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_text
from django.utils.http import is_safe_url, urlsafe_base64_decode
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import UpdateView
from django.views.generic.base import TemplateView

from hijack.views import login_with_id
from two_factor.views import LoginView as TwoFactorLoginView

from wagtail.admin.views.account import password_management_enabled

from .decorators import require_oauth_whitelist
from .forms import BecomeUserForm, ProfileForm


User = get_user_model()


class LoginView(SuccessURLAllowedHostsMixin, TwoFactorLoginView):
    redirect_authenticated_user = False

    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        if self.redirect_authenticated_user and self.request.user.is_authenticated:
            redirect_to = self.get_success_url()
            if redirect_to == self.request.path:
                raise ValueError(
                    "Redirection loop for authenticated user detected. Check that "
                    "your LOGIN_REDIRECT_URL doesn't point to a login page."
                )
            return HttpResponseRedirect(redirect_to)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        url = self.get_redirect_url()
        return url or resolve_url(settings.LOGIN_REDIRECT_URL)

    def get_redirect_url(self):
        """Return the user-originating redirect URL if it's safe."""
        redirect_to = self.request.POST.get(
            self.redirect_field_name,
            self.request.GET.get(self.redirect_field_name, '')
        )
        url_is_safe = is_safe_url(
            url=redirect_to,
            allowed_hosts=self.get_success_url_allowed_hosts(),
            require_https=self.request.is_secure(),
        )
        return redirect_to if url_is_safe else ''

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            next=self.request.GET.get('next', ''),
            **kwargs,
        )


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
            swappable_form = BecomeUserForm()
        else:
            swappable_form = None

        show_change_password = password_management_enabled() and self.request.user.has_usable_password(),

        return super().get_context_data(
            swappable_form=swappable_form,
            show_change_password=show_change_password,
            **kwargs,
        )


@login_required()
def become(request):
    if not request.user.is_apply_staff:
        raise PermissionDenied()

    id = request.POST.get('user')
    if request.POST and id:
        target_user = User.objects.get(pk=id)
        if target_user.is_superuser:
            raise PermissionDenied()

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
                'pk': force_text(urlsafe_base64_decode(uidb64))
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
