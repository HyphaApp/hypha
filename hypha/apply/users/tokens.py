from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.crypto import constant_time_compare
from django.utils.http import base36_to_int


class PasswordlessLoginTokenGenerator(PasswordResetTokenGenerator):
    key_salt = None
    TIMEOUT = None

    def __init__(self) -> None:
        self.key_salt = (
            self.key_salt or "hypha.apply.users.tokens.PasswordlessLoginTokenGenerator"
        )
        self.TIMEOUT = self.TIMEOUT or settings.PASSWORDLESS_LOGIN_TIMEOUT
        super().__init__()

    def check_token(self, user, token):
        """
        Check that a token is correct for a given user.
        """
        if not (user and token):
            return False
        # Parse the token
        try:
            ts_b36, _ = token.split("-")
        except ValueError:
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        for secret in [self.secret, *self.secret_fallbacks]:
            if constant_time_compare(
                self._make_token_with_timestamp(user, ts, secret),
                token,
            ):
                break
        else:
            return False

        # Check the timestamp is within limit.
        if (self._num_seconds(self._now()) - ts) > self.TIMEOUT:
            return False

        return True


class PasswordlessSignupTokenGenerator(PasswordlessLoginTokenGenerator):
    key_salt = None
    TIMEOUT = None

    def __init__(self) -> None:
        self.key_salt = (
            self.key_salt or "hypha.apply.users.tokens.PasswordlessLoginTokenGenerator"
        )
        self.TIMEOUT = self.TIMEOUT or settings.PASSWORDLESS_SIGNUP_TIMEOUT
        super().__init__()

    def _make_hash_value(self, user, timestamp):
        """
        Hash the signup request's primary key, email, and some user state
        that's sure to change after a signup is completed produce a token that is
        invalidated when it's used.

        The token field and modified field will be updated after creating or
        updating the signup request.

        Failing those things, settings.PASSWORDLESS_SIGNUP_TIMEOUT eventually
        invalidates the token.

        Running this data through salted_hmac() prevents password cracking
        attempts using the reset token, provided the secret isn't compromised.
        """
        # Truncate microseconds so that tokens are consistent even if the
        # database doesn't support microseconds.
        modified_timestamp = user.modified.replace(microsecond=0, tzinfo=None)
        return f"{user.pk}{user.token}{modified_timestamp}{timestamp}{user.email}"


class CoApplicantInviteTokenGenerator(PasswordlessLoginTokenGenerator):
    key_salt = None
    TIMEOUT = None

    def __init__(self) -> None:
        self.key_salt = (
            self.key_salt or "hypha.apply.users.tokens.CoApplicantInviteTokenGenerator"
        )
        self.TIMEOUT = self.TIMEOUT or settings.PASSWORDLESS_SIGNUP_TIMEOUT
        super().__init__()

    def _make_hash_value(self, invite, timestamp):
        """
        Hash the signup request's primary key, email, and some user state
        that's sure to change after a signup is completed produce a token that is
        invalidated when it's used.

        The token field and modified field will be updated after creating or
        updating the signup request.

        Failing those things, settings.PASSWORDLESS_SIGNUP_TIMEOUT eventually
        invalidates the token.

        Running this data through salted_hmac() prevents password cracking
        attempts using the reset token, provided the secret isn't compromised.
        """
        return (
            f"{invite.pk}{invite.submission.pk}{timestamp}{invite.invited_user_email}"
        )
