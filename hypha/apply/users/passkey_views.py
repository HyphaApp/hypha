import base64
import json

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, resolve_url
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_POST
from django_ratelimit.decorators import ratelimit
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
    AuthenticatorTransport,
    PublicKeyCredentialDescriptor,
    RegistrationCredential,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from .models import Passkey

SESSION_CHALLENGE_KEY_REGISTER = "webauthn_challenge_register"
SESSION_CHALLENGE_KEY_AUTH = "webauthn_challenge_auth"


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


def _store_challenge(request, challenge: bytes, key: str):
    request.session[key] = base64.b64encode(challenge).decode()


def _load_challenge(request, key: str) -> bytes:
    encoded = request.session.pop(key, None)
    if not encoded:
        raise PermissionDenied("No active WebAuthn challenge.")
    return base64.b64decode(encoded)


# ---------------------------------------------------------------------------
# Registration — requires an authenticated user
# ---------------------------------------------------------------------------


MAX_PASSKEYS_PER_USER = 10


@login_required
@require_POST
@ratelimit(key="user", rate=settings.DEFAULT_RATE_LIMIT, method="POST")
def passkey_register_begin(request):
    user = request.user
    existing_passkeys = list(user.passkeys.all())
    if len(existing_passkeys) >= MAX_PASSKEYS_PER_USER:
        return JsonResponse(
            {"error": f"Maximum of {MAX_PASSKEYS_PER_USER} passkeys allowed"},
            status=400,
        )
    existing = [
        PublicKeyCredentialDescriptor(
            id=base64url_to_bytes(pk.credential_id),
            transports=[AuthenticatorTransport(t) for t in pk.transports] or None,
        )
        for pk in existing_passkeys
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
    _store_challenge(request, options.challenge, SESSION_CHALLENGE_KEY_REGISTER)
    return JsonResponse(json.loads(options_to_json(options)))


@login_required
@require_POST
@ratelimit(key="user", rate=settings.DEFAULT_RATE_LIMIT, method="POST")
def passkey_register_complete(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        challenge = _load_challenge(request, SESSION_CHALLENGE_KEY_REGISTER)
    except PermissionDenied:
        return JsonResponse({"error": "No active WebAuthn challenge"}, status=400)

    try:
        credential = RegistrationCredential(
            id=data["id"],
            raw_id=base64url_to_bytes(data["rawId"]),
            response=AuthenticatorAttestationResponse(
                client_data_json=base64url_to_bytes(data["response"]["clientDataJSON"]),
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
    except Exception:
        return JsonResponse({"error": "Verification failed"}, status=400)

    name = (data.get("name") or "").strip() or timezone.now().strftime(
        "Passkey %Y-%m-%d"
    )
    Passkey.objects.create(
        user=request.user,
        name=name,
        credential_id=bytes_to_base64url(verification.credential_id),
        public_key=bytes_to_base64url(verification.credential_public_key),
        sign_count=verification.sign_count,
        transports=data["response"].get("transports", []),
    )
    return JsonResponse({"status": "ok"})


# ---------------------------------------------------------------------------
# Authentication — public (no session required)
# ---------------------------------------------------------------------------


@require_POST
@ratelimit(key="ip", rate=settings.DEFAULT_RATE_LIMIT, method="POST")
def passkey_auth_begin(request):
    options = generate_authentication_options(
        rp_id=_get_rp_id(request),
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    _store_challenge(request, options.challenge, SESSION_CHALLENGE_KEY_AUTH)
    return JsonResponse(json.loads(options_to_json(options)))


@require_POST
@ratelimit(key="ip", rate=settings.DEFAULT_RATE_LIMIT, method="POST")
def passkey_auth_complete(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        challenge = _load_challenge(request, SESSION_CHALLENGE_KEY_AUTH)
    except PermissionDenied:
        return JsonResponse({"error": "No active WebAuthn challenge"}, status=400)

    try:
        credential_id_b64 = bytes_to_base64url(base64url_to_bytes(data["rawId"]))
    except Exception:
        return JsonResponse({"error": "Invalid credential"}, status=400)

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
                client_data_json=base64url_to_bytes(data["response"]["clientDataJSON"]),
                authenticator_data=base64url_to_bytes(
                    data["response"]["authenticatorData"]
                ),
                signature=base64url_to_bytes(data["response"]["signature"]),
                user_handle=base64url_to_bytes(user_handle) if user_handle else None,
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
    except Exception:
        return JsonResponse({"error": "Verification failed"}, status=400)

    passkey.sign_count = verification.new_sign_count
    passkey.last_used_at = timezone.now()
    passkey.save(update_fields=["sign_count", "last_used_at"])

    user = passkey.user
    user.backend = settings.CUSTOM_AUTH_BACKEND
    login(request, user)
    request.session["passkey_authenticated"] = True

    if data.get("remember_me"):
        request.session.set_expiry(settings.SESSION_COOKIE_AGE_LONG)

    next_url = data.get("next") or resolve_url(settings.LOGIN_REDIRECT_URL)
    if not url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = resolve_url(settings.LOGIN_REDIRECT_URL)
    return JsonResponse({"status": "ok", "redirect_url": next_url})


# ---------------------------------------------------------------------------
# Passkey management — account page
# ---------------------------------------------------------------------------


@login_required
@require_GET
def passkey_list(request):
    passkeys = request.user.passkeys.all()
    return render(request, "users/partials/list.html", {"passkeys": passkeys})


@login_required
@require_POST
def passkey_delete(request, pk):
    passkey = get_object_or_404(Passkey, pk=pk, user=request.user)
    passkey.delete()
    passkeys = request.user.passkeys.all()
    return render(request, "users/partials/list.html", {"passkeys": passkeys})


@login_required
@require_POST
def passkey_rename(request, pk):
    passkey = get_object_or_404(Passkey, pk=pk, user=request.user)
    name = request.POST.get("name", "").strip()
    if name:
        passkey.name = name
        passkey.save(update_fields=["name"])
    passkeys = request.user.passkeys.all()
    return render(request, "users/partials/list.html", {"passkeys": passkeys})
