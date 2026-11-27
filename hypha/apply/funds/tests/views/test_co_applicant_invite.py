import re

from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from hypha.apply.activity.adapters.emails import EmailAdapter
from hypha.apply.activity.messaging import MESSAGES
from hypha.apply.funds.models import CoApplicantInvite
from hypha.apply.funds.models.co_applicants import CoApplicantInviteStatus
from hypha.apply.funds.tests.factories.models import ApplicationSubmissionFactory
from hypha.apply.funds.utils import generate_invite_path
from hypha.apply.users.tests.factories import ApplicantFactory


def make_invite(email):
    return CoApplicantInvite.objects.create(
        submission=ApplicationSubmissionFactory(),
        invited_user_email=email,
        invited_at=timezone.now(),
    )


def logged_in_user_id(client):
    return client.session.get("_auth_user_id")


def accept(client, path):
    return client.post(path, {"action": "accept"})


class TestInviteRecipient:
    def recipients(self, invite):
        return EmailAdapter().recipients(
            MESSAGES.INVITE_COAPPLICANT,
            source=invite.submission,
            user=None,
            related=invite,
        )

    def test_sent_to_matching_accounts_own_address(self, db):
        ApplicantFactory(email="bob@example.com")
        invite = make_invite("Bob@Example.com")

        assert self.recipients(invite) == ["bob@example.com"]

    def test_sent_to_invited_address_without_account(self, db):
        invite = make_invite("new@example.com")

        assert self.recipients(invite) == ["new@example.com"]

    def test_lookalike_is_sent_to_invited_address(self, db):
        ApplicantFactory(email="bob@gmail.com")
        invite = make_invite("bob@gmaıl.com")

        assert self.recipients(invite) == ["bob@gmaıl.com"]


@override_settings(SEND_MESSAGES=True)
def test_invite_email_link_logs_in_matching_account(db, client):
    owner = ApplicantFactory()
    bob = ApplicantFactory(email="bob@example.com")
    submission = ApplicationSubmissionFactory(user=owner)

    client.force_login(owner)
    response = client.post(
        reverse("apply:submissions:invite_co_applicant", kwargs={"pk": submission.pk}),
        {"invited_user_email": "Bob@Example.com", "submission": submission.pk},
    )
    assert response.status_code == 204
    client.logout()

    invite_mails = [m for m in mail.outbox if "co-applicant" in m.subject]
    assert len(invite_mails) == 1
    assert invite_mails[0].to == ["bob@example.com"]

    path = re.search(
        r"/apply/submissions/coapplicants/invite/accept/[^/\s]+/[^/\s]+/",
        invite_mails[0].body,
    )
    accept(client, path.group(0))
    assert logged_in_user_id(client) == str(bob.pk)


class TestAcceptInvite:
    def test_link_for_matching_account_logs_it_in(self, db, client):
        bob = ApplicantFactory(email="bob@example.com")
        invite = make_invite("Bob@Example.com")
        path = generate_invite_path(invite, bob.email)

        accept(client, path)

        assert logged_in_user_id(client) == str(bob.pk)

    def test_link_for_invited_address_does_not_log_in_other_account(self, db, client):
        # The link went to the typed address, not to the account.
        ApplicantFactory(email="bob@example.com")
        invite = make_invite("Bob@Example.com")
        path = generate_invite_path(invite, invite.invited_user_email)

        response = client.get(path)
        assert response.context["is_valid"] is False
        accept(client, path)
        assert logged_in_user_id(client) is None

    def test_account_created_after_invite_with_other_address(self, db, client):
        invite = make_invite("Bob@Example.com")
        path = generate_invite_path(invite, invite.invited_user_email)
        ApplicantFactory(email="bob@example.com")

        accept(client, path)

        assert logged_in_user_id(client) is None
        invite.refresh_from_db()
        assert invite.status == CoApplicantInviteStatus.PENDING

    def test_account_created_after_invite_with_same_address(self, db, client):
        invite = make_invite("bob@example.com")
        path = generate_invite_path(invite, invite.invited_user_email)
        bob = ApplicantFactory(email="bob@example.com")

        accept(client, path)

        assert logged_in_user_id(client) == str(bob.pk)

    def test_account_email_changed_after_invite(self, db, client):
        bob = ApplicantFactory(email="bob@example.com")
        invite = make_invite("bob@example.com")
        path = generate_invite_path(invite, bob.email)
        bob.email = "bob@elsewhere.com"
        bob.save()
        other = ApplicantFactory(email="Bob@example.com")

        accept(client, path)

        assert logged_in_user_id(client) is None
        assert other.pk
