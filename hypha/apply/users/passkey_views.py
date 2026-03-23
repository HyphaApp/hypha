import base64
import json

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.structs import (
    AuthenticationCredential,
    AuthenticatorAssertionResponse,
    AuthenticatorAttestationResponse,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    RegistrationCredential,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from .models import Passkey

User = get_user_model()

SESSION_CHALLENGE_KEY = "webauthn_challenge"


def _get_rp_id(request):
    rp_id = getattr(settings, "WEBAUTHN_RP_ID", None)
    if rp_id:
        return rp_id
    return request.get_host().split(":")[0]


def _get_rp_name():
    return getattr(settings, "WEBAUTHN_RP_NAME", None) or settings.ORG_LONG_NAME


def _get_origin(request):
    origin = getattr(settings, "WEBAUTHN_ORIGIN", None)
    if origin:
        return origin
    scheme = "https" if request.is_secure() else "http"
    return f"{scheme}://{request.get_host()}"


def _store_challenge(request, challenge: bytes):
    request.session[SESSION_CHALLENGE_KEY] = base64.b64encode(challenge).decode()


def _load_challenge(request) -> bytes:
    encoded = request.session.pop(SESSION_CHALLENGE_KEY, None)
    if not encoded:
        raise PermissionDenied("No active WebAuthn challenge.")
    return base64.b64decode(encoded)


# ---------------------------------------------------------------------------
# Registration — requires an authenticated user
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class PasskeyRegisterBeginView(View):
    def post(self, request):
        user = request.user
        existing = [
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(pk.credential_id))
            for pk in user.passkeys.all()
        ]
        options = generate_registration_options(
            rp_id=_get_rp_id(request),
            rp_name=_get_rp_name(),
            user_id=str(user.pk).encode(),
            user_name=user.email,
            user_display_name=user.get_full_name() or user.email,
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement.REQUIRED,
                user_verification=UserVerificationRequirement.REQUIRED,
            ),
            exclude_credentials=existing,
        )
        _store_challenge(request, options.challenge)
        return JsonResponse(json.loads(options_to_json(options)))


@method_decorator(login_required, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class PasskeyRegisterCompleteView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        try:
            challenge = _load_challenge(request)
        except PermissionDenied as e:
            return JsonResponse({"error": str(e)}, status=400)

        try:
            credential = RegistrationCredential(
                id=data["id"],
                raw_id=base64url_to_bytes(data["rawId"]),
                response=AuthenticatorAttestationResponse(
                    client_data_json=base64url_to_bytes(
                        data["response"]["clientDataJSON"]
                    ),
                    attestation_object=base64url_to_bytes(
                        data["response"]["attestationObject"]
                    ),
                    transports=data["response"].get("transports", []),
                ),
            )
            verification = verify_registration_response(
                credential=credential,
                expected_challenge=challenge,
                expected_rp_id=_get_rp_id(request),
                expected_origin=_get_origin(request),
                require_user_verification=True,
            )
        except Exception as exc:
            return JsonResponse({"error": str(exc)}, status=400)

        name = (data.get("name") or "").strip() or timezone.now().strftime(
            "Passkey %Y-%m-%d"
        )
        Passkey.objects.create(
            user=request.user,
            name=name,
            credential_id=bytes_to_base64url(verification.credential_id),
            public_key=bytes_to_base64url(verification.credential_public_key),
            sign_count=verification.sign_count,
        )
        return JsonResponse({"status": "ok"})


# ---------------------------------------------------------------------------
# Authentication — public (no session required)
# ---------------------------------------------------------------------------


@method_decorator(csrf_protect, name="dispatch")
class PasskeyAuthBeginView(View):
    def post(self, request):
        options = generate_authentication_options(
            rp_id=_get_rp_id(request),
            user_verification=UserVerificationRequirement.REQUIRED,
        )
        _store_challenge(request, options.challenge)
        return JsonResponse(json.loads(options_to_json(options)))


@method_decorator(csrf_protect, name="dispatch")
class PasskeyAuthCompleteView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        try:
            challenge = _load_challenge(request)
        except PermissionDenied as e:
            return JsonResponse({"error": str(e)}, status=400)

        credential_id_b64 = bytes_to_base64url(base64url_to_bytes(data["rawId"]))
        try:
            passkey = Passkey.objects.select_related("user").get(
                credential_id=credential_id_b64
            )
        except Passkey.DoesNotExist:
            return JsonResponse({"error": "Unknown credential"}, status=400)

        try:
            user_handle = data["response"].get("userHandle")
            credential = AuthenticationCredential(
                id=data["id"],
                raw_id=base64url_to_bytes(data["rawId"]),
                response=AuthenticatorAssertionResponse(
                    client_data_json=base64url_to_bytes(
                        data["response"]["clientDataJSON"]
                    ),
                    authenticator_data=base64url_to_bytes(
                        data["response"]["authenticatorData"]
                    ),
                    signature=base64url_to_bytes(data["response"]["signature"]),
                    user_handle=base64url_to_bytes(user_handle)
                    if user_handle
                    else None,
                ),
            )
            verification = verify_authentication_response(
                credential=credential,
                expected_challenge=challenge,
                expected_rp_id=_get_rp_id(request),
                expected_origin=_get_origin(request),
                credential_public_key=base64url_to_bytes(passkey.public_key),
                credential_current_sign_count=passkey.sign_count,
                require_user_verification=True,
            )
        except Exception as exc:
            return JsonResponse({"error": str(exc)}, status=400)

        passkey.sign_count = verification.new_sign_count
        passkey.last_used_at = timezone.now()
        passkey.save(update_fields=["sign_count", "last_used_at"])

        user = passkey.user
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        request.session["passkey_authenticated"] = True

        next_url = request.POST.get("next") or data.get("next") or "/"
        return JsonResponse({"status": "ok", "redirect_url": next_url})


# ---------------------------------------------------------------------------
# Passkey management — account page
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class PasskeyListView(View):
    template_name = "users/partials/list.html"

    def get(self, request):
        passkeys = request.user.passkeys.all()
        return render(request, self.template_name, {"passkeys": passkeys})


@method_decorator(login_required, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class PasskeyDeleteView(View):
    def post(self, request, pk):
        passkey = get_object_or_404(Passkey, pk=pk, user=request.user)
        passkey.delete()
        passkeys = request.user.passkeys.all()
        return render(request, "users/partials/list.html", {"passkeys": passkeys})


@method_decorator(login_required, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class PasskeyRenameView(View):
    def post(self, request, pk):
        passkey = get_object_or_404(Passkey, pk=pk, user=request.user)
        name = request.POST.get("name", "").strip()
        if name:
            passkey.name = name
            passkey.save(update_fields=["name"])
        passkeys = request.user.passkeys.all()
        return render(request, "users/partials/list.html", {"passkeys": passkeys})
