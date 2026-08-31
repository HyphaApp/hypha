from django.test import override_settings
from django.urls import reverse

from hypha.apply.funds.models.submissions import AnonymizedSubmission
from hypha.apply.funds.tests.factories.models import ApplicationSubmissionFactory
from hypha.apply.funds.workflows import DRAFT_STATE
from hypha.apply.users.tests.factories import (
    AdminFactory,
    ApplicantFactory,
)


def test_delete_submission_view_login(db, client):
    submission = ApplicationSubmissionFactory(status="internal_review")
    delete_url = reverse("apply:submissions:delete", kwargs={"pk": submission.pk})
    res = client.get(delete_url)

    # check login required
    assert res.status_code == 302
    assert f"/auth/?next={delete_url}" in res.url


def test_submission_delete_by_admin(db, client):
    # Check admin can delete submission
    user = AdminFactory()
    submission = ApplicationSubmissionFactory()

    client.force_login(user)
    delete_url = reverse("apply:submissions:delete", kwargs={"pk": submission.pk})
    res = client.get(delete_url)
    assert res.status_code == 200
    assert "<form" in res.content.decode()
    assert f'action="{delete_url}"' in res.content.decode()

    res = client.post(delete_url)
    assert res.status_code == 302
    assert res.url == "/apply/submissions/all/"

    # Check submission is deleted
    res = client.get(delete_url)
    assert res.status_code == 404


@override_settings(SUBMISSION_ANONYMIZATION_ENABLED=True)
def test_submission_delete_by_admin_anonymization_enabled(db, client):
    # Check admin can delete submission
    user = AdminFactory()
    submission = ApplicationSubmissionFactory()

    client.force_login(user)
    delete_url = reverse("apply:submissions:delete", kwargs={"pk": submission.pk})
    res = client.get(delete_url)
    assert res.status_code == 200
    assert "<form" in res.content.decode()
    assert f'action="{delete_url}"' in res.content.decode()

    res = client.post(delete_url)
    assert res.status_code == 302
    assert res.url == "/apply/submissions/all/"

    # Check submission is deleted
    res = client.get(delete_url)
    assert res.status_code == 404

    # Ensure no anonymized submission was created
    assert AnonymizedSubmission.objects.all().count() == 0


@override_settings(SUBMISSION_ANONYMIZATION_ENABLED=True)
def test_submission_anonymize_by_admin_anonymization_enabled(db, client):
    user = AdminFactory()
    submission = ApplicationSubmissionFactory()
    expected_value = submission.form_data["value"]

    client.force_login(user)
    anonymize_url = reverse("apply:submissions:anonymize", kwargs={"pk": submission.pk})
    res = client.get(anonymize_url)
    assert res.status_code == 200
    assert "<form" in res.content.decode()

    res = client.post(anonymize_url)
    assert res.status_code == 302
    assert res.url == "/apply/submissions/all/"

    # Check submission is deleted
    res = client.get(anonymize_url)
    assert res.status_code == 404

    # Ensure a new anonymized submission was created
    assert AnonymizedSubmission.objects.all().count() == 1

    last_anonymized = AnonymizedSubmission.objects.last()
    assert last_anonymized.value == expected_value


# --- SubmissionAnonymizeView tests ---


def test_anonymize_view_login_required(db, client):
    submission = ApplicationSubmissionFactory(status="internal_review")
    url = reverse("apply:submissions:anonymize", kwargs={"pk": submission.pk})
    res = client.get(url)

    assert res.status_code == 302
    assert f"/auth/?next={url}" in res.url


def test_anonymize_view_forbidden_for_applicant(db, client):
    user = ApplicantFactory()
    submission = ApplicationSubmissionFactory(status="internal_review")

    client.force_login(user)
    url = reverse("apply:submissions:anonymize", kwargs={"pk": submission.pk})
    res = client.get(url)

    assert res.status_code == 403


def test_anonymize_view_get_renders_confirmation(db, client):
    user = AdminFactory()
    submission = ApplicationSubmissionFactory(status="internal_review")

    client.force_login(user)
    url = reverse("apply:submissions:anonymize", kwargs={"pk": submission.pk})
    res = client.get(url)

    assert res.status_code == 200
    assert "<form" in res.content.decode()
    assert f'action="{url}"' in res.content.decode()


def test_anonymize_view_post_creates_anonymized_record(db, client):
    user = AdminFactory()
    submission = ApplicationSubmissionFactory(status="internal_review")
    expected_value = submission.form_data["value"]

    client.force_login(user)
    url = reverse("apply:submissions:anonymize", kwargs={"pk": submission.pk})
    res = client.post(url)

    assert res.status_code == 302
    assert AnonymizedSubmission.objects.count() == 1
    anon = AnonymizedSubmission.objects.last()
    assert anon.value == expected_value


def test_anonymize_view_post_deletes_original_submission(db, client):
    user = AdminFactory()
    submission = ApplicationSubmissionFactory(status="internal_review")
    pk = submission.pk

    client.force_login(user)
    url = reverse("apply:submissions:anonymize", kwargs={"pk": pk})
    client.post(url)

    res = client.get(url)
    assert res.status_code == 404


def test_anonymize_view_post_draft_skips_messenger(db, client):
    """Anonymizing a draft should not fire the ANONYMIZE_SUBMISSION messenger."""
    user = AdminFactory()
    submission = ApplicationSubmissionFactory(status=DRAFT_STATE)

    client.force_login(user)
    url = reverse("apply:submissions:anonymize", kwargs={"pk": submission.pk})
    res = client.post(url)

    assert res.status_code == 302
    # Draft submissions are still anonymized (record created, original deleted)
    assert AnonymizedSubmission.objects.count() == 1


def test_anonymize_view_redirects_to_submissions_list(db, client):
    user = AdminFactory()
    submission = ApplicationSubmissionFactory(status="internal_review")

    client.force_login(user)
    url = reverse("apply:submissions:anonymize", kwargs={"pk": submission.pk})
    res = client.post(url)

    assert res.status_code == 302
    assert res.url == "/apply/submissions/all/"


# --- SubmissionDeleteView tests ---


def test_submission_delete_by_applicant(db, client):
    user = ApplicantFactory()
    submission = ApplicationSubmissionFactory(user=user, status=DRAFT_STATE)

    client.force_login(user)
    delete_url = reverse("apply:submissions:delete", kwargs={"pk": submission.pk})
    res = client.get(delete_url)
    assert res.status_code == 200
    assert "<form" in res.content.decode()
    assert f'action="{delete_url}"' in res.content.decode()

    res = client.post(delete_url)
    assert res.status_code == 302
    assert res.url == "/dashboard/"

    # Check submission is deleted
    res = client.get(delete_url)
    assert res.status_code == 404


def test_applicant_cannot_delete_own_non_draft(db, client):
    user = ApplicantFactory()
    submission = ApplicationSubmissionFactory(user=user, status="internal_review")

    client.force_login(user)
    delete_url = reverse("apply:submissions:delete", kwargs={"pk": submission.pk})
    res = client.get(delete_url)
    assert res.status_code == 403


def test_applicant_cannot_delete_another_applicants_draft(db, client):
    user = ApplicantFactory()
    other_submission = ApplicationSubmissionFactory(status=DRAFT_STATE)

    client.force_login(user)
    delete_url = reverse("apply:submissions:delete", kwargs={"pk": other_submission.pk})
    res = client.get(delete_url)
    assert res.status_code == 403
