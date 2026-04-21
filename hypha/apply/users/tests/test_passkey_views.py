"""Tests for WebAuthn passkey views (passkey_views.py)."""

import base64
import json
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from webauthn.helpers import bytes_to_base64url
from webauthn.helpers.exceptions import InvalidAuthenticationResponse

from ..models import Passkey
from ..passkey_views import (
    MAX_PASSKEYS_PER_USER,
    SESSION_CHALLENGE_KEY_AUTH,
    SESSION_CHALLENGE_KEY_REGISTER,
)
from .factories import UserFactory

AUTH_BEGIN_URL = reverse("users:passkey_auth_begin")
AUTH_COMPLETE_URL = reverse("users:passkey_auth_complete")
REGISTER_BEGIN_URL = reverse("users:passkey_register_begin")
REGISTER_COMPLETE_URL = reverse("users:passkey_register_complete")
PASSKEY_LIST_URL = reverse("users:passkey_list")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_passkey(
    user, credential_id=None, public_key=None, name="Test Passkey", **kwargs
):
    """Create a Passkey for a user with sensible defaults."""
    kwargs.setdefault("sign_count", 0)
    kwargs.setdefault("transports", ["internal"])
    return Passkey.objects.create(
        user=user,
        name=name,
        # base64url of b"test-cred-id" and b"test-pubkey"
        credential_id=credential_id or bytes_to_base64url(b"test-cred-id"),
        public_key=public_key or bytes_to_base64url(b"test-pubkey"),
        **kwargs,
    )


def set_challenge(client, key, challenge_bytes=b"test-challenge"):
    """Store a base64-encoded WebAuthn challenge in the test client session."""
    session = client.session
    session[key] = base64.b64encode(challenge_bytes).decode()
    session.save()


# ---------------------------------------------------------------------------
# Registration begin
# ---------------------------------------------------------------------------


@override_settings(RATELIMIT_ENABLE=False)
class TestPasskeyRegisterBegin(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_requires_login(self):
        self.client.logout()
        response = self.client.post(REGISTER_BEGIN_URL)
        self.assertEqual(response.status_code, 302)

    def test_requires_post(self):
        response = self.client.get(REGISTER_BEGIN_URL)
        self.assertEqual(response.status_code, 405)

    def test_returns_registration_options(self):
        response = self.client.post(REGISTER_BEGIN_URL)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("challenge", data)
        self.assertIn("rp", data)
        self.assertIn("user", data)

    def test_stores_challenge_in_session(self):
        self.client.post(REGISTER_BEGIN_URL)
        self.assertIn(SESSION_CHALLENGE_KEY_REGISTER, self.client.session)

    def test_returns_400_when_max_passkeys_reached(self):
        for i in range(MAX_PASSKEYS_PER_USER):
            make_passkey(
                self.user, credential_id=bytes_to_base64url(f"cred{i}".encode())
            )
        response = self.client.post(REGISTER_BEGIN_URL)
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())


# ---------------------------------------------------------------------------
# Registration complete
# ---------------------------------------------------------------------------


@override_settings(RATELIMIT_ENABLE=False)
class TestPasskeyRegisterComplete(TestCase):
    CHALLENGE = b"test-challenge-register"

    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)

    def _set_challenge(self):
        set_challenge(self.client, SESSION_CHALLENGE_KEY_REGISTER, self.CHALLENGE)

    def _payload(self, name="My Key"):
        return {
            "id": bytes_to_base64url(b"new-cred"),
            "rawId": bytes_to_base64url(b"new-cred"),
            "name": name,
            "response": {
                "clientDataJSON": bytes_to_base64url(b"clientdata"),
                "attestationObject": bytes_to_base64url(b"attestation"),
                "transports": ["internal"],
            },
            "type": "public-key",
        }

    def test_requires_login(self):
        self.client.logout()
        self._set_challenge()
        response = self.client.post(
            REGISTER_COMPLETE_URL,
            data=json.dumps(self._payload()),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)

    def test_invalid_json_returns_400(self):
        self._set_challenge()
        response = self.client.post(
            REGISTER_COMPLETE_URL,
            data="not-valid-json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_missing_challenge_returns_400(self):
        # No challenge placed in session
        response = self.client.post(
            REGISTER_COMPLETE_URL,
            data=json.dumps(self._payload()),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    @patch("hypha.apply.users.passkey_views.verify_registration_response")
    def test_successful_registration_saves_passkey(self, mock_verify):
        mock_verify.return_value = MagicMock(
            credential_id=b"saved-cred-id",
            credential_public_key=b"saved-pubkey",
            sign_count=0,
        )
        self._set_challenge()
        response = self.client.post(
            REGISTER_COMPLETE_URL,
            data=json.dumps(self._payload(name="My Key")),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(self.user.passkeys.count(), 1)
        self.assertEqual(self.user.passkeys.first().name, "My Key")

    @patch("hypha.apply.users.passkey_views.verify_registration_response")
    def test_name_is_truncated_to_128_chars(self, mock_verify):
        mock_verify.return_value = MagicMock(
            credential_id=b"cred",
            credential_public_key=b"pubkey",
            sign_count=0,
        )
        self._set_challenge()
        long_name = "x" * 200
        response = self.client.post(
            REGISTER_COMPLETE_URL,
            data=json.dumps(self._payload(name=long_name)),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.user.passkeys.first().name, "x" * 128)

    @patch("hypha.apply.users.passkey_views.verify_registration_response")
    def test_empty_name_gets_date_default(self, mock_verify):
        mock_verify.return_value = MagicMock(
            credential_id=b"cred",
            credential_public_key=b"pubkey",
            sign_count=0,
        )
        self._set_challenge()
        response = self.client.post(
            REGISTER_COMPLETE_URL,
            data=json.dumps(self._payload(name="")),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        passkey = self.user.passkeys.first()
        self.assertTrue(passkey.name.startswith("Passkey "))

    @patch("hypha.apply.users.passkey_views.verify_registration_response")
    def test_verification_failure_returns_400_and_saves_nothing(self, mock_verify):
        mock_verify.side_effect = Exception("crypto error")
        self._set_challenge()
        response = self.client.post(
            REGISTER_COMPLETE_URL,
            data=json.dumps(self._payload()),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertEqual(self.user.passkeys.count(), 0)

    def test_challenge_is_consumed_and_cannot_be_replayed(self):
        """The registration challenge must be single-use."""
        self._set_challenge()
        # First call consumes the challenge (will fail verification, that's OK)
        self.client.post(
            REGISTER_COMPLETE_URL,
            data=json.dumps(self._payload()),
            content_type="application/json",
        )
        # Second call with the same payload must fail with "no challenge" error
        response = self.client.post(
            REGISTER_COMPLETE_URL,
            data=json.dumps(self._payload()),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("challenge", response.json()["error"].lower())


# ---------------------------------------------------------------------------
# Authentication begin
# ---------------------------------------------------------------------------


@override_settings(RATELIMIT_ENABLE=False)
class TestPasskeyAuthBegin(TestCase):
    def test_requires_post(self):
        response = self.client.get(AUTH_BEGIN_URL)
        self.assertEqual(response.status_code, 405)

    def test_returns_authentication_options(self):
        response = self.client.post(AUTH_BEGIN_URL)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("challenge", data)
        self.assertIn("rpId", data)

    def test_stores_challenge_in_session(self):
        self.client.post(AUTH_BEGIN_URL)
        self.assertIn(SESSION_CHALLENGE_KEY_AUTH, self.client.session)

    def test_accessible_without_login(self):
        response = self.client.post(AUTH_BEGIN_URL)
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# Authentication complete
# ---------------------------------------------------------------------------

CRED_ID = bytes_to_base64url(b"auth-cred-id")
PUBKEY = bytes_to_base64url(b"auth-pubkey")


@override_settings(RATELIMIT_ENABLE=False)
class TestPasskeyAuthComplete(TestCase):
    CHALLENGE = b"test-challenge-auth"

    def setUp(self):
        self.user = UserFactory()
        self.passkey = make_passkey(
            self.user,
            credential_id=CRED_ID,
            public_key=PUBKEY,
            sign_count=0,
        )

    def _set_challenge(self):
        set_challenge(self.client, SESSION_CHALLENGE_KEY_AUTH, self.CHALLENGE)

    def _payload(self, **overrides):
        payload = {
            "id": CRED_ID,
            "rawId": CRED_ID,
            "response": {
                "clientDataJSON": bytes_to_base64url(b"clientdata"),
                "authenticatorData": bytes_to_base64url(b"authdata"),
                "signature": bytes_to_base64url(b"sig"),
            },
            "type": "public-key",
        }
        payload.update(overrides)
        return payload

    def test_requires_post(self):
        response = self.client.get(AUTH_COMPLETE_URL)
        self.assertEqual(response.status_code, 405)

    def test_invalid_json_returns_400(self):
        self._set_challenge()
        response = self.client.post(
            AUTH_COMPLETE_URL,
            data="not-json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_missing_challenge_returns_400(self):
        response = self.client.post(
            AUTH_COMPLETE_URL,
            data=json.dumps(self._payload()),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_unknown_credential_returns_400(self):
        self._set_challenge()
        unknown_id = bytes_to_base64url(b"no-such-cred")
        response = self.client.post(
            AUTH_COMPLETE_URL,
            data=json.dumps(self._payload(id=unknown_id, rawId=unknown_id)),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    @patch("hypha.apply.users.passkey_views.verify_authentication_response")
    def test_successful_auth_logs_in_user(self, mock_verify):
        mock_verify.return_value = MagicMock(new_sign_count=1)
        self._set_challenge()
        response = self.client.post(
            AUTH_COMPLETE_URL,
            data=json.dumps(self._payload()),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertIn("redirect_url", response.json())
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    @patch("hypha.apply.users.passkey_views.verify_authentication_response")
    def test_successful_auth_sets_passkey_session_flag(self, mock_verify):
        mock_verify.return_value = MagicMock(new_sign_count=1)
        self._set_challenge()
        self.client.post(
            AUTH_COMPLETE_URL,
            data=json.dumps(self._payload()),
            content_type="application/json",
        )
        self.assertTrue(self.client.session.get("passkey_authenticated"))

    @patch("hypha.apply.users.passkey_views.verify_authentication_response")
    def test_successful_auth_updates_sign_count(self, mock_verify):
        mock_verify.return_value = MagicMock(new_sign_count=42)
        self._set_challenge()
        self.client.post(
            AUTH_COMPLETE_URL,
            data=json.dumps(self._payload()),
            content_type="application/json",
        )
        self.passkey.refresh_from_db()
        self.assertEqual(self.passkey.sign_count, 42)

    @patch("hypha.apply.users.passkey_views.verify_authentication_response")
    def test_successful_auth_updates_last_used_at(self, mock_verify):
        mock_verify.return_value = MagicMock(new_sign_count=1)
        self._set_challenge()
        self.client.post(
            AUTH_COMPLETE_URL,
            data=json.dumps(self._payload()),
            content_type="application/json",
        )
        self.passkey.refresh_from_db()
        self.assertIsNotNone(self.passkey.last_used_at)

    @patch("hypha.apply.users.passkey_views.verify_authentication_response")
    def test_open_redirect_falls_back_to_login_redirect(self, mock_verify):
        mock_verify.return_value = MagicMock(new_sign_count=1)
        self._set_challenge()
        payload = self._payload()
        payload["next"] = "https://evil.example.com/steal"
        response = self.client.post(
            AUTH_COMPLETE_URL,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        redirect_url = response.json()["redirect_url"]
        self.assertNotIn("evil.example.com", redirect_url)

    @patch("hypha.apply.users.passkey_views.verify_authentication_response")
    def test_valid_next_url_is_passed_through(self, mock_verify):
        mock_verify.return_value = MagicMock(new_sign_count=1)
        self._set_challenge()
        payload = self._payload()
        payload["next"] = "/apply/"
        response = self.client.post(
            AUTH_COMPLETE_URL,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["redirect_url"], "/apply/")

    def test_user_handle_mismatch_returns_400(self):
        """A userHandle that doesn't match the passkey owner must be rejected."""
        other_user = UserFactory()
        # Encode other_user's pk as the handle — view decodes and compares against
        # str(passkey.user.pk).encode(), which is this user's pk.
        wrong_handle = bytes_to_base64url(str(other_user.pk).encode())
        self._set_challenge()
        payload = self._payload()
        payload["response"]["userHandle"] = wrong_handle
        response = self.client.post(
            AUTH_COMPLETE_URL,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    @patch("hypha.apply.users.passkey_views.verify_authentication_response")
    def test_verification_failure_returns_400(self, mock_verify):
        mock_verify.side_effect = InvalidAuthenticationResponse("bad signature")
        self._set_challenge()
        response = self.client.post(
            AUTH_COMPLETE_URL,
            data=json.dumps(self._payload()),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_challenge_is_consumed_and_cannot_be_replayed(self):
        """The auth challenge must be single-use (popped from session)."""
        self._set_challenge()
        # First call pops the challenge
        self.client.post(
            AUTH_COMPLETE_URL,
            data=json.dumps(self._payload()),
            content_type="application/json",
        )
        # Second call must fail because challenge is gone
        response = self.client.post(
            AUTH_COMPLETE_URL,
            data=json.dumps(self._payload()),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("challenge", response.json()["error"].lower())


# ---------------------------------------------------------------------------
# Passkey list
# ---------------------------------------------------------------------------


class TestPasskeyList(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(PASSKEY_LIST_URL)
        self.assertEqual(response.status_code, 302)

    def test_requires_get(self):
        response = self.client.post(PASSKEY_LIST_URL)
        self.assertEqual(response.status_code, 405)

    def test_returns_200_with_no_passkeys(self):
        response = self.client.get(PASSKEY_LIST_URL)
        self.assertEqual(response.status_code, 200)

    def test_shows_own_passkeys(self):
        make_passkey(self.user, name="My MacBook")
        response = self.client.get(PASSKEY_LIST_URL)
        self.assertContains(response, "My MacBook")

    def test_does_not_show_other_users_passkeys(self):
        other = UserFactory()
        make_passkey(other, name="Someone Elses Key")
        response = self.client.get(PASSKEY_LIST_URL)
        self.assertNotContains(response, "Someone Elses Key")


# ---------------------------------------------------------------------------
# Passkey delete
# ---------------------------------------------------------------------------


class TestPasskeyDelete(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_requires_login(self):
        self.client.logout()
        passkey = make_passkey(self.user)
        url = reverse("users:passkey_delete", args=[passkey.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_deletes_own_passkey(self):
        passkey = make_passkey(self.user)
        url = reverse("users:passkey_delete", args=[passkey.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Passkey.objects.filter(pk=passkey.pk).exists())

    def test_cannot_delete_other_users_passkey(self):
        other = UserFactory()
        passkey = make_passkey(other)
        url = reverse("users:passkey_delete", args=[passkey.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Passkey.objects.filter(pk=passkey.pk).exists())

    def test_returns_updated_passkey_list_partial(self):
        passkey = make_passkey(self.user)
        url = reverse("users:passkey_delete", args=[passkey.pk])
        response = self.client.post(url)
        self.assertTemplateUsed(response, "users/partials/list.html")


# ---------------------------------------------------------------------------
# Passkey rename
# ---------------------------------------------------------------------------


class TestPasskeyRename(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_requires_login(self):
        self.client.logout()
        passkey = make_passkey(self.user)
        url = reverse("users:passkey_rename", args=[passkey.pk])
        response = self.client.post(url, {"name": "New Name"})
        self.assertEqual(response.status_code, 302)

    def test_renames_own_passkey(self):
        passkey = make_passkey(self.user, name="Old Name")
        url = reverse("users:passkey_rename", args=[passkey.pk])
        response = self.client.post(url, {"name": "New Name"})
        self.assertEqual(response.status_code, 200)
        passkey.refresh_from_db()
        self.assertEqual(passkey.name, "New Name")

    def test_cannot_rename_other_users_passkey(self):
        other = UserFactory()
        passkey = make_passkey(other, name="Original")
        url = reverse("users:passkey_rename", args=[passkey.pk])
        response = self.client.post(url, {"name": "Hacked Name"})
        self.assertEqual(response.status_code, 404)
        passkey.refresh_from_db()
        self.assertEqual(passkey.name, "Original")

    def test_whitespace_only_name_is_ignored(self):
        passkey = make_passkey(self.user, name="Original")
        url = reverse("users:passkey_rename", args=[passkey.pk])
        response = self.client.post(url, {"name": "   "})
        self.assertEqual(response.status_code, 200)
        passkey.refresh_from_db()
        self.assertEqual(passkey.name, "Original")

    def test_name_is_trimmed(self):
        passkey = make_passkey(self.user)
        url = reverse("users:passkey_rename", args=[passkey.pk])
        self.client.post(url, {"name": "  Trimmed  "})
        passkey.refresh_from_db()
        self.assertEqual(passkey.name, "Trimmed")

    def test_name_is_truncated_to_128_chars(self):
        passkey = make_passkey(self.user)
        url = reverse("users:passkey_rename", args=[passkey.pk])
        self.client.post(url, {"name": "x" * 200})
        passkey.refresh_from_db()
        self.assertEqual(passkey.name, "x" * 128)

    def test_returns_updated_passkey_list_partial(self):
        passkey = make_passkey(self.user)
        url = reverse("users:passkey_rename", args=[passkey.pk])
        response = self.client.post(url, {"name": "Updated"})
        self.assertTemplateUsed(response, "users/partials/list.html")


# ---------------------------------------------------------------------------
# Middleware — passkey_authenticated session flag bypasses ENFORCE_TWO_FACTOR
# ---------------------------------------------------------------------------


@override_settings(ENFORCE_TWO_FACTOR=True)
class TestPasskeyMiddlewareBypass(TestCase):
    def test_passkey_session_flag_bypasses_2fa_enforcement(self):
        user = UserFactory()
        self.client.force_login(user)
        session = self.client.session
        session["passkey_authenticated"] = True
        session.save()

        # The middleware should let the request through — account page is always accessible.
        response = self.client.get(reverse("users:account"), follow=True)
        self.assertNotContains(response, "Permission Denied")

    def test_without_passkey_flag_unverified_user_is_blocked(self):
        user = UserFactory()
        self.client.force_login(user)
        # No passkey_authenticated flag and no OTP device

        response = self.client.get(settings.LOGIN_REDIRECT_URL, follow=True)
        self.assertContains(response, "Permission Denied")
