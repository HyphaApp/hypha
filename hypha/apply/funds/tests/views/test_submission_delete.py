from django.test import override_settings
from django.urls import reverse

from hypha.apply.funds.models.submissions import ApplicationSubmissionSkeleton
from hypha.apply.funds.tests.factories.models import ApplicationSubmissionFactory
from hypha.apply.funds.workflows import DRAFT_STATE
from hypha.apply.users.tests.factories import AdminFactory, ApplicantFactory


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
    assert "id_anon_or_delete" not in res.content.decode()

    res = client.post(delete_url, data={"delete": "delete", "anon_or_delete": "DELETE"})
    assert res.status_code == 302
    assert res.url == "/apply/submissions/all/"

    # Check submission is deleted
    res = client.get(delete_url)
    assert res.status_code == 404


@override_settings(SUBMISSION_SKELETONING_ENABLED=True)
def test_submission_delete_by_admin_skeleton_enabled(db, client):
    # Check admin can delete submission
    user = AdminFactory()
    submission = ApplicationSubmissionFactory()

    client.force_login(user)
    delete_url = reverse("apply:submissions:delete", kwargs={"pk": submission.pk})
    res = client.get(delete_url)
    assert res.status_code == 200
    assert "<form" in res.content.decode()
    assert f'action="{delete_url}"' in res.content.decode()

    res = client.post(delete_url, data={"delete": "delete", "anon_or_delete": "DELETE"})
    assert res.status_code == 302
    assert res.url == "/apply/submissions/all/"

    # Check submission is deleted
    res = client.get(delete_url)
    assert res.status_code == 404

    # Ensure no skeleton submission was created
    assert ApplicationSubmissionSkeleton.objects.all().count() == 0


@override_settings(SUBMISSION_SKELETONING_ENABLED=True)
def test_submission_skeleton_by_admin_skeleton_enabled(db, client):
    user = AdminFactory()
    submission = ApplicationSubmissionFactory()

    client.force_login(user)
    delete_url = reverse("apply:submissions:delete", kwargs={"pk": submission.pk})
    res = client.get(delete_url)
    assert res.status_code == 200
    assert "<form" in res.content.decode()
    assert f'action="{delete_url}"' in res.content.decode()

    # Add the skeleton option to the delete form
    res = client.post(
        delete_url, data={"delete": "delete", "anon_or_delete": "ANONYMIZE"}
    )
    assert res.status_code == 302
    assert res.url == "/apply/submissions/all/"

    # Check submission is deleted
    res = client.get(delete_url)
    assert res.status_code == 404

    # Ensure a new skeleton submission was created
    assert ApplicationSubmissionSkeleton.objects.all().count() == 1

    last_skeleton = ApplicationSubmissionSkeleton.objects.last()
    assert last_skeleton.value == submission.form_data["value"]


def test_submission_delete_by_applicant(db, client):
    user = ApplicantFactory()
    submission = ApplicationSubmissionFactory(user=user, status=DRAFT_STATE)

    client.force_login(user)
    delete_url = reverse("apply:submissions:delete", kwargs={"pk": submission.pk})
    res = client.get(delete_url)
    assert res.status_code == 200
    assert "<form" in res.content.decode()
    assert f'action="{delete_url}"' in res.content.decode()

    res = client.post(delete_url, data={"delete": "delete"})
    assert res.status_code == 302
    assert res.url == "/dashboard/"

    # Check submission is deleted
    res = client.get(delete_url)
    assert res.status_code == 404

    # Check user can't delete submission in other states
    submission = ApplicationSubmissionFactory(user=user, status="internal_review")
    delete_url = reverse("apply:submissions:delete", kwargs={"pk": submission.pk})
    res = client.get(delete_url)
    assert res.status_code == 403
