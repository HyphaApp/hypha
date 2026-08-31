"""Additional tests for User model, UserQuerySet, and related models."""

from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.utils import translation

from ..models import ConfirmAccessToken, PendingSignup, User
from ..roles import (
    APPROVER_GROUP_NAME,
    TEAMADMIN_GROUP_NAME,
)
from .factories import (
    ApplicantFactory,
    ApproverFactory,
    CommunityReviewerFactory,
    ContractingFactory,
    FinanceFactory,
    ReviewerFactory,
    StaffFactory,
    SuperUserFactory,
    UserFactory,
)


@override_settings(LANGUAGE_CODE="en")
class TestUserQuerySet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = StaffFactory()
        cls.reviewer = ReviewerFactory()
        cls.applicant = ApplicantFactory()
        cls.finance = FinanceFactory()
        cls.contracting = ContractingFactory()
        cls.community_reviewer = CommunityReviewerFactory()
        cls.approver = ApproverFactory()

    def test_staff_queryset(self):
        qs = User.objects.staff()
        self.assertIn(self.staff, qs)
        self.assertNotIn(self.applicant, qs)

    def test_reviewers_queryset(self):
        qs = User.objects.reviewers()
        self.assertIn(self.reviewer, qs)
        self.assertNotIn(self.staff, qs)

    def test_applicants_queryset(self):
        qs = User.objects.applicants()
        self.assertIn(self.applicant, qs)
        self.assertNotIn(self.staff, qs)

    def test_finances_queryset(self):
        qs = User.objects.finances()
        self.assertIn(self.finance, qs)
        self.assertNotIn(self.applicant, qs)

    def test_contracting_queryset(self):
        qs = User.objects.contracting()
        self.assertIn(self.contracting, qs)
        self.assertNotIn(self.applicant, qs)

    def test_community_reviewers_queryset(self):
        qs = User.objects.community_reviewers()
        self.assertIn(self.community_reviewer, qs)
        self.assertNotIn(self.staff, qs)

    def test_approvers_queryset(self):
        qs = User.objects.approvers()
        self.assertIn(self.approver, qs)
        self.assertNotIn(self.applicant, qs)

    def test_active_filters_inactive(self):
        inactive_user = UserFactory(is_active=False)
        qs = User.objects.active()
        self.assertNotIn(inactive_user, qs)

    def test_staff_admin_queryset(self):
        admin = UserFactory()
        admin_group, _ = Group.objects.get_or_create(name=TEAMADMIN_GROUP_NAME)
        admin.groups.add(admin_group)
        qs = User.objects.staff_admin()
        self.assertIn(admin, qs)
        self.assertNotIn(self.applicant, qs)

    # Requires compiling the translations first:
    # uv run --with-requirements=requirements/dev.txt python -m django compilemessages --ignore=.venv/* --locale=ru
    def test_translated_is_apply_staff(self):
        self.assertTrue(self.staff.is_apply_staff)
        translation.activate("fr")
        del self.staff.is_apply_staff  # Clear cached value
        self.assertTrue(self.staff.is_apply_staff)


@override_settings(LANGUAGE_CODE="en")
class TestUserModel(TestCase):
    def test_get_display_name_with_full_name(self):
        user = UserFactory(full_name="Jane Doe", email="jane@example.com")
        self.assertEqual(user.get_display_name(), "Jane Doe")

    def test_get_display_name_without_full_name(self):
        user = UserFactory(full_name="", email="jane@example.com")
        self.assertEqual(user.get_display_name(), "jane")

    def test_get_short_name_returns_email_local_part(self):
        user = UserFactory(email="alice@example.com")
        self.assertEqual(user.get_short_name(), "alice")

    def test_str_returns_display_name(self):
        user = UserFactory(full_name="Bob Smith")
        self.assertEqual(str(user), "Bob Smith")

    def test_repr(self):
        user = UserFactory(full_name="Bob Smith", email="bob@example.com")
        self.assertIn("Bob Smith", repr(user))
        self.assertIn("bob@example.com", repr(user))

    def test_get_absolute_url(self):
        user = UserFactory()
        url = user.get_absolute_url()
        self.assertIn(str(user.id), url)

    def test_is_org_faculty_true_for_staff(self):
        staff = StaffFactory()
        self.assertTrue(staff.is_org_faculty)

    def test_is_org_faculty_true_for_finance(self):
        finance = FinanceFactory()
        self.assertTrue(finance.is_org_faculty)

    def test_is_org_faculty_true_for_contracting(self):
        contracting = ContractingFactory()
        self.assertTrue(contracting.is_org_faculty)

    def test_is_org_faculty_false_for_applicant(self):
        applicant = ApplicantFactory()
        self.assertFalse(applicant.is_org_faculty)

    def test_can_access_dashboard_for_staff(self):
        self.assertTrue(StaffFactory().can_access_dashboard)

    def test_can_access_dashboard_for_reviewer(self):
        self.assertTrue(ReviewerFactory().can_access_dashboard)

    def test_can_access_dashboard_for_applicant(self):
        self.assertTrue(ApplicantFactory().can_access_dashboard)

    def test_can_access_dashboard_false_for_plain_user(self):
        # A user with no groups cannot access the dashboard
        user = UserFactory()
        self.assertFalse(user.can_access_dashboard)

    def test_is_contracting_approver_true(self):
        user = ContractingFactory()
        approver_group, _ = Group.objects.get_or_create(name=APPROVER_GROUP_NAME)
        user.groups.add(approver_group)
        # Clear cache
        if "is_approver" in user.__dict__:
            del user.__dict__["is_approver"]
        if "is_contracting_approver" in user.__dict__:
            del user.__dict__["is_contracting_approver"]
        if "roles" in user.__dict__:
            del user.__dict__["roles"]
        user = User.objects.get(pk=user.pk)
        self.assertTrue(user.is_contracting_approver)

    def test_is_contracting_approver_false_for_non_contracting(self):
        approver = ApproverFactory()
        self.assertFalse(approver.is_contracting_approver)

    def test_get_role_names_staff(self):
        staff = StaffFactory()
        roles = [str(r) for r in staff.get_role_names()]
        self.assertIn("Staff", roles)

    def test_get_role_names_reviewer(self):
        reviewer = ReviewerFactory()
        roles = [str(r) for r in reviewer.get_role_names()]
        self.assertIn("Reviewer", roles)

    def test_get_role_names_empty_for_plain_user(self):
        user = UserFactory()
        roles = user.get_role_names()
        self.assertEqual(roles, [])

    def test_superuser_is_apply_staff(self):
        superuser = SuperUserFactory()
        self.assertTrue(superuser.is_apply_staff)

    def test_superuser_is_apply_staff_admin(self):
        superuser = SuperUserFactory()
        self.assertTrue(superuser.is_apply_staff_admin)


class TestUserManagerCreateUser(TestCase):
    def test_create_user_sets_defaults(self):
        user = User.objects.create_user(email="new@example.com", password="pass")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_requires_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="pass")

    def test_create_user_duplicate_email_raises(self):
        UserFactory(email="dup@example.com")
        with self.assertRaises(ValueError):
            User.objects.create_user(email="dup@example.com", password="pass")

    def test_create_superuser_requires_is_staff_true(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="su@example.com", password="pass", is_staff=False
            )

    def test_create_superuser_requires_is_superuser_true(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="su@example.com", password="pass", is_superuser=False
            )


class TestPendingSignup(TestCase):
    def test_str_includes_email(self):
        signup = PendingSignup.objects.create(
            email="pending@example.com", token="abc123token456"
        )
        self.assertIn("pending@example.com", str(signup))


class TestConfirmAccessToken(TestCase):
    def test_str_includes_user_email(self):
        user = UserFactory(email="tokenuser@example.com")
        token = ConfirmAccessToken.objects.create(user=user, token="123456")
        self.assertIn("tokenuser@example.com", str(token))
