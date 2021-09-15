import re
from datetime import timedelta

from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from hypha.apply.activity.models import TEAM, Activity
from hypha.apply.determinations.tests.factories import DeterminationFactory
from hypha.apply.funds.tests.factories import (
    ApplicationRevisionFactory,
    ApplicationSubmissionFactory,
    AssignedReviewersFactory,
    AssignedWithRoleReviewersFactory,
    InvitedToProposalFactory,
    LabSubmissionFactory,
    ReminderFactory,
    ReviewerRoleFactory,
    ScreeningStatusFactory,
    SealedRoundFactory,
    SealedSubmissionFactory,
)
from hypha.apply.funds.workflow import INITIAL_STATE
from hypha.apply.home.factories import ApplySiteFactory
from hypha.apply.projects.models import Project
from hypha.apply.projects.tests.factories import ProjectFactory
from hypha.apply.review.tests.factories import ReviewFactory
from hypha.apply.users.tests.factories import (
    ApplicantFactory,
    CommunityReviewerFactory,
    PartnerFactory,
    ReviewerFactory,
    StaffFactory,
    SuperUserFactory,
)
from hypha.apply.utils.testing import make_request
from hypha.apply.utils.testing.tests import BaseViewTestCase

from ..models import (
    ApplicationRevision,
    ApplicationSubmission,
    ReviewerSettings,
    ScreeningStatus,
)
from ..views import SubmissionDetailSimplifiedView, SubmissionDetailView
from .factories import CustomFormFieldsFactory


def prepare_form_data(submission, **kwargs):
    data = submission.raw_data

    for field, value in kwargs.items():
        # convert named fields into  id
        field_id = submission.field(field).id
        data[field_id] = value

    return CustomFormFieldsFactory.form_response(submission.form_fields, data)


class BaseSubmissionViewTestCase(BaseViewTestCase):
    url_name = 'funds:submissions:{}'
    base_view_name = 'detail'

    def get_kwargs(self, instance):
        return {'pk': instance.id}


class TestStaffSubmissionView(BaseSubmissionViewTestCase):
    user_factory = StaffFactory

    @classmethod
    def setUpTestData(cls):
        cls.submission = ApplicationSubmissionFactory()
        super().setUpTestData()

    def __setUp__(self):
        self.refresh(self.submission)

    def test_can_view_a_submission(self):
        response = self.get_page(self.submission)
        self.assertContains(response, self.submission.title)

    def test_can_view_a_lab_submission(self):
        submission = LabSubmissionFactory()
        response = self.get_page(submission)
        self.assertContains(response, submission.title)

    def test_can_progress_phase(self):
        next_status = 'internal_review'
        self.post_page(self.submission, {'form-submitted-progress_form': '', 'action': next_status})

        submission = self.refresh(self.submission)
        self.assertEqual(submission.status, next_status)

    def test_redirected_to_determination(self):
        submission = ApplicationSubmissionFactory(status='concept_review_discussion', workflow_stages=2, lead=self.user)
        response = self.post_page(submission, {'form-submitted-progress_form': '', 'action': 'invited_to_proposal'})

        # Invited for proposal is a a determination, so this will redirect to the determination form.
        url = self.url_from_pattern('funds:submissions:determinations:form', kwargs={'submission_pk': submission.id})
        self.assertRedirects(response, f"{url}?action=invited_to_proposal")

    def test_new_form_after_progress(self):
        submission = ApplicationSubmissionFactory(status='invited_to_proposal', workflow_stages=2, lead=self.user)
        stage = submission.stage
        DeterminationFactory(submission=submission, accepted=True)

        request = make_request(self.user, method='get', site=submission.page.get_site())
        submission.progress_stage_when_possible(self.user, request)

        submission = self.refresh(submission)
        new_stage = submission.stage

        self.assertNotEqual(stage, new_stage)

        get_forms = submission.get_from_parent('get_defined_fields')
        self.assertEqual(submission.form_fields, get_forms(new_stage))
        self.assertNotEqual(submission.form_fields, get_forms(stage))

    def test_cant_progress_stage_if_not_lead(self):
        submission = ApplicationSubmissionFactory(status='concept_review_discussion', workflow_stages=2)
        self.post_page(submission, {'form-submitted-progress_form': '', 'action': 'invited_to_proposal'})

        submission = self.refresh(submission)

        self.assertEqual(submission.status, 'concept_review_discussion')
        self.assertIsNone(submission.next)

    def test_not_redirected_if_determination_submitted(self):
        submission = ApplicationSubmissionFactory(lead=self.user)
        DeterminationFactory(submission=submission, rejected=True, submitted=True)

        self.post_page(submission, {'form-submitted-progress_form': '', 'action': 'rejected'})

        submission = self.refresh(submission)
        self.assertEqual(submission.status, 'rejected')

    def test_not_redirected_if_wrong_determination_selected(self):
        submission = ApplicationSubmissionFactory(lead=self.user)
        DeterminationFactory(submission=submission, accepted=True, submitted=True)

        response = self.post_page(submission, {'form-submitted-progress_form': '', 'action': 'rejected'})
        self.assertContains(response, 'you tried to progress')

        submission = self.refresh(submission)
        self.assertNotEqual(submission.status, 'accepted')
        self.assertNotEqual(submission.status, 'rejected')

    def test_cant_access_edit_button_when_applicant_editing(self):
        submission = ApplicationSubmissionFactory(status='more_info')
        response = self.get_page(submission)
        self.assertNotContains(response, self.url(submission, 'edit', absolute=False))

    def test_can_access_edit_button(self):
        response = self.get_page(self.submission)
        self.assertContains(response, self.url(self.submission, 'edit', absolute=False))

    def test_can_access_edit(self):
        response = self.get_page(self.submission, 'edit')
        self.assertContains(response, self.submission.title)

    def test_previous_and_next_appears_on_page(self):
        proposal = InvitedToProposalFactory()
        response = self.get_page(proposal)
        self.assertContains(response, self.url(proposal.previous, absolute=False))

        response = self.get_page(proposal.previous)
        self.assertContains(response, self.url(proposal, absolute=False))

    def test_can_edit_submission(self):
        old_status = self.submission.status
        new_title = 'A new Title'
        data = prepare_form_data(self.submission, title=new_title)
        response = self.post_page(self.submission, {'submit': True, **data}, 'edit')

        url = self.url(self.submission)

        self.assertRedirects(response, url)
        submission = self.refresh(self.submission)

        # Staff edits don't affect the status
        self.assertEqual(old_status, submission.status)
        self.assertEqual(new_title, submission.title)

    def test_not_included_fields_render(self):
        submission = ApplicationSubmissionFactory(form_fields__exclude__checkbox=True)
        response = self.get_page(submission)
        self.assertNotContains(response, 'check_one')

    def test_can_screen_submission(self):
        ScreeningStatus.objects.all().delete()
        screening_outcome1 = ScreeningStatusFactory()
        screening_outcome1.yes = True
        screening_outcome1.save()
        screening_outcome2 = ScreeningStatusFactory()
        screening_outcome2.yes = True
        screening_outcome2.default = True
        screening_outcome2.save()
        self.submission.screening_statuses.clear()
        self.submission.screening_statuses.add(screening_outcome2)
        self.post_page(self.submission, {'form-submitted-screening_form': '', 'screening_statuses': [screening_outcome1.id, screening_outcome2.id]})
        submission = self.refresh(self.submission)
        self.assertEqual(submission.screening_statuses.count(), 2)

    def test_can_view_submission_screening_block(self):
        ScreeningStatus.objects.all().delete()
        screening_outcome1 = ScreeningStatusFactory()
        screening_outcome1.yes = True
        screening_outcome1.default = True
        screening_outcome1.yes = True
        screening_outcome1.save()
        screening_outcome2 = ScreeningStatusFactory()
        screening_outcome2.yes = False
        screening_outcome2.default = True
        screening_outcome2.save()
        self.submission.screening_statuses.clear()
        response = self.get_page(self.submission)
        self.assertContains(response, 'Screening status')

    def test_cant_view_submission_screening_block(self):
        """
        If defaults are not set screening status block is not visible
        """
        ScreeningStatus.objects.all().delete()
        self.submission.screening_statuses.clear()
        response = self.get_page(self.submission)
        self.assertNotContains(response, 'Screening status')

    def test_can_create_project(self):
        # check submission doesn't already have a Project
        with self.assertRaisesMessage(Project.DoesNotExist, 'ApplicationSubmission has no project.'):
            self.submission.project

        self.post_page(self.submission, {
            'form-submitted-project_form': '',
            'submission': self.submission.id,
        })

        project = Project.objects.order_by('-pk').first()
        submission = ApplicationSubmission.objects.get(pk=self.submission.pk)

        self.assertTrue(hasattr(submission, 'project'))
        self.assertEquals(submission.project.id, project.id)

    def test_can_see_add_determination_primary_action(self):
        def assert_add_determination_displayed(submission, button_text):
            response = self.get_page(submission)
            # Ignore whitespace (including line breaks) in button text
            pattern = re.compile(rf'\s*{button_text}\s*')
            buttons = BeautifulSoup(response.content, 'html5lib').find(class_='js-actions-sidebar').find_all('a', class_='button--primary', text=pattern)
            self.assertEqual(len(buttons), 1)

        submission = ApplicationSubmissionFactory(status='determination')

        # Phase: ready-for-determination, no determination
        # "Add determination" should be displayed
        assert_add_determination_displayed(submission, 'Add determination')

        # Phase: ready-for-determination, draft determination
        # "Complete draft determination" should be displayed
        DeterminationFactory(submission=submission, author=self.user, accepted=True, submitted=False)
        assert_add_determination_displayed(submission, 'Complete draft determination')

    def test_cant_see_add_determination_primary_action(self):
        def assert_add_determination_not_displayed(submission, button_text):
            response = self.get_page(submission)
            # Ignore whitespace (including line breaks) in button text
            pattern = re.compile(rf'\s*{button_text}\s*')
            buttons = BeautifulSoup(response.content, 'html5lib').find(class_='js-actions-sidebar').find_all('a', class_='button--primary', text=pattern)
            self.assertEqual(len(buttons), 0)

        submission = ApplicationSubmissionFactory()

        # Phase: received / in_discussion
        # "Add determination" should not be displayed
        # "Complete draft determination" should not be displayed
        assert_add_determination_not_displayed(submission, 'Add determination')
        assert_add_determination_not_displayed(submission, 'Complete draft determination')

        # Phase: accepted
        # "Add determination" should not be displayed
        # "Complete draft determination" should not be displayed
        submission.perform_transition('accepted', self.user)
        assert_add_determination_not_displayed(submission, 'Add determination')
        assert_add_determination_not_displayed(submission, 'Complete draft determination')

    def test_screen_application_primary_action_is_displayed(self):
        ScreeningStatus.objects.all().delete()
        # Submission not screened
        screening_outcome = ScreeningStatusFactory()
        screening_outcome.yes = False
        screening_outcome.default = True
        screening_outcome.save()
        self.submission.screening_statuses.clear()
        self.submission.screening_statuses.add(screening_outcome)
        response = self.get_page(self.submission)
        buttons = BeautifulSoup(response.content, 'html5lib').find(class_='sidebar').find_all('a', text='Screen application')
        self.assertEqual(len(buttons), 1)
        self.submission.screening_statuses.clear()

    def test_screen_application_primary_action_is_not_displayed(self):
        response = self.get_page(self.submission)
        buttons = BeautifulSoup(response.content, 'html5lib').find(class_='sidebar').find_all('a', text='Screen application')
        self.assertEqual(len(buttons), 0)

    def test_can_see_create_review_primary_action(self):
        def assert_create_review_displayed(submission, button_text):
            response = self.get_page(submission)
            # Ignore whitespace (including line breaks) in button text
            pattern = re.compile(rf'\s*{button_text}\s*')
            buttons = BeautifulSoup(response.content, 'html5lib').find(class_='js-actions-sidebar').find_all('a', class_='button--primary', text=pattern)
            self.assertEqual(len(buttons), 1)

        submission = ApplicationSubmissionFactory(with_external_review=True, status='ext_internal_review')

        # Phase: internal_review, no review
        # "Add a review" should be displayed
        assert_create_review_displayed(submission, 'Add a review')

        # Phase: internal_review, draft review created
        # "Complete draft review" should be displayed
        review = ReviewFactory(submission=submission, author__reviewer=self.user, is_draft=True)
        assert_create_review_displayed(submission, 'Complete draft review')
        review.delete()

        # Phase: external_review, no review
        # "Add a review" should be displayed
        submission.perform_transition('ext_post_review_discussion', self.user)
        submission.perform_transition('ext_external_review', self.user)
        assert_create_review_displayed(submission, 'Add a review')

        # Phase: external_review, draft review created
        # "Complete draft review" should be displayed
        ReviewFactory(submission=submission, author__reviewer=self.user, is_draft=True)
        assert_create_review_displayed(submission, 'Complete draft review')

    def test_cant_see_create_review_primary_action(self):
        def assert_create_review_not_displayed(submission, button_text):
            response = self.get_page(submission)
            # Ignore whitespace (including line breaks) in button text
            pattern = re.compile(rf'\s*{button_text}\s*')
            buttons = BeautifulSoup(response.content, 'html5lib').find(class_='js-actions-sidebar').find_all('a', class_='button--primary', text=pattern)
            self.assertEqual(len(buttons), 0)

        submission = ApplicationSubmissionFactory(with_external_review=True)

        # Phase: received / in_discussion
        # "Add a review" should not be displayed
        # "Complete draft review" should not be displayed
        assert_create_review_not_displayed(submission, 'Add a review')
        assert_create_review_not_displayed(submission, 'Complete draft review')

        # Phase: internal_review, review completed
        # "Add a review" should not be displayed
        # "Update draft review" should not be displayed
        submission.perform_transition('ext_internal_review', self.user)
        ReviewFactory(submission=submission, author__reviewer=self.user, is_draft=False)
        assert_create_review_not_displayed(submission, 'Add a review')
        assert_create_review_not_displayed(submission, 'Complete draft review')

        # Phase: external_review, review completed
        # "Add a review" should not be displayed
        # "Update draft review" should not be displayed
        submission.perform_transition('ext_post_review_discussion', self.user)
        submission.perform_transition('ext_external_review', self.user)
        assert_create_review_not_displayed(submission, 'Add a review')
        assert_create_review_not_displayed(submission, 'Complete draft review')

    def test_can_see_assign_reviewers_primary_action(self):
        def assert_assign_reviewers_displayed(submission):
            response = self.get_page(submission)
            buttons = BeautifulSoup(response.content, 'html5lib').find(class_='sidebar').find_all('a', class_='button--primary', text='Assign reviewers')
            self.assertEqual(len(buttons), 1)

        submission = ApplicationSubmissionFactory(status='internal_review')
        reviewer_role_a = ReviewerRoleFactory()
        reviewer_role_b = ReviewerRoleFactory()

        # Phase: internal_review - no reviewers assigned
        # Assign reviewers should be displayed
        assert_assign_reviewers_displayed(submission)

        # Phase: internal_review - not all reviewer types assigned
        # Assign reviewers should be displayed
        AssignedReviewersFactory(submission=submission, reviewer=ReviewerFactory(), role=reviewer_role_a)
        assert_assign_reviewers_displayed(submission)

        # Phase: external_review - no reviewers assigned
        # Assign reviewers should be displayed
        submission = ApplicationSubmissionFactory(with_external_review=True, status='ext_external_review')
        assert_assign_reviewers_displayed(submission)

        # Phase: external_review - all reviewers types assigned
        # Assign reviewers should still be displayed
        AssignedReviewersFactory(submission=submission, reviewer=ReviewerFactory(), role=reviewer_role_a)
        AssignedReviewersFactory(submission=submission, reviewer=ReviewerFactory(), role=reviewer_role_b)
        assert_assign_reviewers_displayed(submission)

    def test_cant_see_assign_reviewers_primary_action(self):
        def assert_assign_reviewers_not_displayed(submission):
            response = self.get_page(submission)
            buttons = BeautifulSoup(response.content, 'html5lib').find(class_='sidebar').find_all('a', class_='button--primary', text='Assign reviewers')
            self.assertEqual(len(buttons), 0)

        submission = ApplicationSubmissionFactory()
        reviewer_role = ReviewerRoleFactory()
        # Phase: received / in_discussion
        # Assign reviewers should not be displayed
        assert_assign_reviewers_not_displayed(submission)

        # Phase: internal_review - all reviewer types assigned
        # Assign reviewers should not be displayed
        AssignedReviewersFactory(submission=submission, reviewer=ReviewerFactory(), role=reviewer_role)
        assert_assign_reviewers_not_displayed(submission)

    def test_can_see_assign_reviewers_secondary_action(self):
        def assert_assign_reviewers_secondary_displayed(submission):
            response = self.get_page(submission)
            buttons = BeautifulSoup(response.content, 'html5lib').find(class_='sidebar').find_all('a', class_='button--white', text='Reviewers')
            self.assertEqual(len(buttons), 1)

        submission = ApplicationSubmissionFactory()
        reviewer_role = ReviewerRoleFactory()

        # Phase: received / in_discussion
        assert_assign_reviewers_secondary_displayed(submission)

        # Phase: internal_review - no reviewers assigned
        submission.perform_transition('internal_review', self.user)
        assert_assign_reviewers_secondary_displayed(submission)

        # Phase: internal_review - all reviewer types assigned
        AssignedReviewersFactory(submission=submission, reviewer=ReviewerFactory(), role=reviewer_role)
        assert_assign_reviewers_secondary_displayed(submission)

    def test_can_see_view_determination_primary_action(self):
        def assert_view_determination_displayed(submission):
            response = self.get_page(submission)
            buttons = BeautifulSoup(response.content, 'html5lib').find(class_='js-actions-sidebar').find_all('a', class_='button--primary', text='View determination')
            self.assertEqual(len(buttons), 1)

        # Phase: accepted
        submission = ApplicationSubmissionFactory(status='accepted')
        DeterminationFactory(submission=submission, author=self.user, accepted=True, submitted=True)
        assert_view_determination_displayed(submission)

        # Phase: rejected
        submission = ApplicationSubmissionFactory(status='rejected')
        DeterminationFactory(submission=submission, author=self.user, rejected=True, submitted=True)
        assert_view_determination_displayed(submission)

    def test_cant_see_view_determination_primary_action(self):
        def assert_view_determination_not_displayed(submission):
            response = self.get_page(submission)
            buttons = BeautifulSoup(response.content, 'html5lib').find(class_='js-actions-sidebar').find_all('a', class_='button--primary', text='View determination')
            self.assertEqual(len(buttons), 0)

        # Phase: received / in_discussion
        submission = ApplicationSubmissionFactory()
        assert_view_determination_not_displayed(submission)

        # Phase: ready-for-determination, no determination
        submission.perform_transition('determination', self.user)
        assert_view_determination_not_displayed(submission)

        # Phase: ready-for-determination, draft determination
        DeterminationFactory(submission=submission, author=self.user, accepted=True, submitted=False)
        assert_view_determination_not_displayed(submission)

    def test_cant_see_application_draft_status(self):
        factory = RequestFactory()
        submission = ApplicationSubmissionFactory(status='draft')
        ProjectFactory(submission=submission)

        request = factory.get(f'/submission/{submission.pk}')
        request.user = StaffFactory()

        with self.assertRaises(Http404):
            SubmissionDetailView.as_view()(request, pk=submission.pk)

    def test_applicant_can_see_application_draft_status(self):
        factory = RequestFactory()
        user = ApplicantFactory()
        submission = ApplicationSubmissionFactory(status='draft', user=user)
        ProjectFactory(submission=submission)

        request = factory.get(f'/submission/{submission.pk}')
        request.user = user

        response = SubmissionDetailView.as_view()(request, pk=submission.pk)
        self.assertEqual(response.status_code, 200)


class TestReviewersUpdateView(BaseSubmissionViewTestCase):
    user_factory = StaffFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.staff = StaffFactory.create_batch(4)
        cls.reviewers = ReviewerFactory.create_batch(4)
        cls.roles = ReviewerRoleFactory.create_batch(2)

    def post_form(self, submission, reviewer_roles=list(), reviewers=list()):
        data = {
            'form-submitted-reviewer_form': '',
            'reviewer_reviewers': [r.id for r in reviewers]
        }
        data.update(
            **{
                f'role_reviewer_{slugify(str(role))}': reviewer.id
                for role, reviewer in zip(self.roles, reviewer_roles)
            }
        )
        return self.post_page(submission, data)

    def test_lead_can_add_staff_single(self):
        submission = ApplicationSubmissionFactory(lead=self.user)

        self.post_form(submission, reviewer_roles=[self.staff[0]])

        self.assertCountEqual(submission.reviewers.all(), [self.staff[0]])

    def test_lead_can_change_staff_single(self):
        submission = ApplicationSubmissionFactory(lead=self.user)
        AssignedWithRoleReviewersFactory(role=self.roles[0], submission=submission, reviewer=self.staff[0])
        self.assertCountEqual(submission.reviewers.all(), [self.staff[0]])

        self.post_form(submission, reviewer_roles=[self.staff[1]])

        self.assertCountEqual(submission.reviewers.all(), [self.staff[1]])
        self.assertEqual(submission.assigned.with_roles().first().reviewer, self.staff[1])

    def test_lead_cant_add_reviewers_single(self):
        submission = ApplicationSubmissionFactory(lead=self.user)

        self.post_form(submission, reviewers=self.reviewers)

        self.assertCountEqual(submission.reviewers.all(), [])

    def test_lead_can_add_reviewers_for_proposal(self):
        submission = InvitedToProposalFactory(lead=self.user)

        self.post_form(submission, reviewers=self.reviewers)

        self.assertCountEqual(submission.reviewers.all(), self.reviewers)

    def test_lead_can_remove_reviewers_for_proposal(self):
        submission = InvitedToProposalFactory(lead=self.user, reviewers=self.reviewers)
        self.assertCountEqual(submission.reviewers.all(), self.reviewers)

        self.post_form(submission)

        self.assertCountEqual(submission.reviewers.all(), [])

    def test_lead_can_remove_some_reviewers_for_proposal(self):
        submission = InvitedToProposalFactory(lead=self.user, reviewers=self.reviewers)
        self.assertCountEqual(submission.reviewers.all(), self.reviewers)

        self.post_form(submission, reviewers=self.reviewers[0:2])

        self.assertCountEqual(submission.reviewers.all(), self.reviewers[0:2])

    def test_staff_cant_add_reviewers_proposal(self):
        submission = ApplicationSubmissionFactory()

        self.post_form(submission, reviewers=self.reviewers)

        self.assertCountEqual(submission.reviewers.all(), [])

    def test_staff_cant_remove_reviewers_proposal(self):
        submission = ApplicationSubmissionFactory(reviewers=self.reviewers)
        self.assertCountEqual(submission.reviewers.all(), self.reviewers)

        self.post_form(submission, reviewers=[])

        self.assertCountEqual(submission.reviewers.all(), self.reviewers)

    def test_lead_can_change_role_reviewer_and_review_remains(self):
        submission = ApplicationSubmissionFactory()
        AssignedWithRoleReviewersFactory(role=self.roles[0], submission=submission, reviewer=self.staff[0])

        # Add a review from that staff reviewer
        ReviewFactory(submission=submission, author__reviewer=self.staff[0], author__staff=True)

        # Assign a different reviewer to the same role
        self.post_form(submission, reviewer_roles=[self.staff[1]])

        # Make sure that the ex-role-reviewer is still assigned record
        self.assertCountEqual(submission.reviewers.all(), self.staff[0:2])

    def test_can_be_made_role_and_not_duplciated(self):
        submission = ApplicationSubmissionFactory()

        ReviewFactory(submission=submission, author__reviewer=self.staff[0], author__staff=True)

        self.post_form(submission, reviewer_roles=[self.staff[0]])
        self.assertCountEqual(submission.reviewers.all(), [self.staff[0]])

    def test_can_remove_external_reviewer_and_review_remains(self):
        submission = InvitedToProposalFactory(lead=self.user)
        reviewer = self.reviewers[0]
        AssignedReviewersFactory(submission=submission, reviewer=reviewer)
        ReviewFactory(submission=submission, author__reviewer=reviewer)

        self.post_form(submission, reviewers=[])

        self.assertCountEqual(submission.reviewers.all(), [reviewer])

    def test_can_add_external_reviewer_and_review_remains(self):
        submission = InvitedToProposalFactory(lead=self.user)
        reviewer = self.reviewers[0]
        AssignedReviewersFactory(submission=submission, reviewer=reviewer)
        ReviewFactory(submission=submission, author__reviewer=reviewer)

        self.post_form(submission, reviewers=[self.reviewers[1]])

        self.assertCountEqual(submission.reviewers.all(), [reviewer, self.reviewers[1]])


class TestReviewerSubmissionView(BaseSubmissionViewTestCase):
    user_factory = ReviewerFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.applicant = ApplicantFactory()
        cls.reviewer_role = ReviewerRoleFactory()
        apply_site = ApplySiteFactory()
        cls.reviewer_settings, _ = ReviewerSettings.objects.get_or_create(site_id=apply_site.id)
        cls.reviewer_settings.use_settings = True
        cls.reviewer_settings.save()

    def test_cant_see_add_determination_primary_action(self):
        def assert_add_determination_not_displayed(submission, button_text):
            response = self.get_page(submission)
            # Ignore whitespace (including line breaks) in button text
            pattern = re.compile(rf'\s*{button_text}\s*')
            buttons = BeautifulSoup(response.content, 'html5lib').find_all('a', class_='button--primary', text=pattern)
            self.assertEqual(len(buttons), 0)

        submission = ApplicationSubmissionFactory(status='determination', user=self.applicant, reviewers=[self.user])

        # Phase: ready-for-determination, no determination
        # "Add determination" should not be displayed
        # "Complete draft determination" should not be displayed
        assert_add_determination_not_displayed(submission, 'Add determination')
        assert_add_determination_not_displayed(submission, 'Complete draft determination')

        # Phase: ready-for-determination, draft determination
        # "Add determination" should not be displayed
        # "Complete draft determination" should not be displayed
        DeterminationFactory(submission=submission, accepted=True, submitted=False)
        assert_add_determination_not_displayed(submission, 'Add determination')
        assert_add_determination_not_displayed(submission, 'Complete draft determination')

    def test_can_see_create_review_primary_action(self):
        def assert_create_review_displayed(submission, button_text):
            response = self.get_page(submission)
            # Ignore whitespace (including line breaks) in button text
            pattern = re.compile(rf'\s*{button_text}\s*')
            buttons = BeautifulSoup(response.content, 'html5lib').find(class_='js-actions-sidebar').find_all('a', class_='button--primary', text=pattern)
            self.assertEqual(len(buttons), 1)

        submission = ApplicationSubmissionFactory(with_external_review=True, status='ext_external_review', user=self.applicant, reviewers=[self.user])

        # Phase: external_review, no review
        # "Add a review" should be displayed
        submission.perform_transition('ext_post_review_discussion', self.user)
        submission.perform_transition('ext_external_review', self.user)
        assert_create_review_displayed(submission, 'Add a review')

        # Phase: external_review, draft review created
        # "Complete draft review" should be displayed
        ReviewFactory(submission=submission, author__reviewer=self.user, is_draft=True)
        assert_create_review_displayed(submission, 'Complete draft review')

    def test_cant_see_create_review_primary_action(self):
        def assert_create_review_not_displayed(submission, button_text):
            response = self.get_page(submission)
            # Ignore whitespace (including line breaks) in button text
            pattern = re.compile(rf'\s*{button_text}\s*')
            buttons = BeautifulSoup(response.content, 'html5lib').find_all('a', class_='button--primary', text=pattern)
            self.assertEqual(len(buttons), 0)

        submission = ApplicationSubmissionFactory(with_external_review=True, user=self.applicant, reviewers=[self.user])

        # Phase: received / in_discussion
        # "Add a review" should not be displayed
        # "Complete draft review" should not be displayed
        assert_create_review_not_displayed(submission, 'Add a review')
        assert_create_review_not_displayed(submission, 'Complete draft review')

        # Phase: internal_review, only viewable by staff users
        # "Add a review" should not be displayed
        # "Update draft review" should not be displayed
        submission.perform_transition('ext_internal_review', self.user)
        assert_create_review_not_displayed(submission, 'Add a review')
        assert_create_review_not_displayed(submission, 'Complete draft review')

        # Phase: external_review, review completed
        # "Add a review" should not be displayed
        # "Update draft review" should not be displayed
        submission.perform_transition('ext_post_review_discussion', self.user)
        submission.perform_transition('ext_external_review', self.user)
        ReviewFactory(submission=submission, author__reviewer=self.user, is_draft=False)
        assert_create_review_not_displayed(submission, 'Add a review')
        assert_create_review_not_displayed(submission, 'Complete draft review')

    def test_cant_see_assign_reviewers_primary_action(self):
        submission = ApplicationSubmissionFactory(status='internal_review', user=self.applicant, reviewers=[self.user])
        response = self.get_page(submission)

        buttons = BeautifulSoup(response.content, 'html5lib').find(class_='sidebar').find_all('a', class_='button--primary', text='Assign reviewers')
        self.assertEqual(len(buttons), 0)

    def test_cant_see_assign_reviewers_secondary_action(self):
        submission = ApplicationSubmissionFactory(status='internal_review', user=self.applicant, reviewers=[self.user])
        response = self.get_page(submission)
        buttons = BeautifulSoup(response.content, 'html5lib').find(class_='sidebar').find_all('a', class_='button--white', text='Reviewers')
        self.assertEqual(len(buttons), 0)

    def test_can_see_view_determination_primary_action(self):
        def assert_view_determination_displayed(submission):
            response = self.get_page(submission)
            buttons = BeautifulSoup(response.content, 'html5lib').find(class_='js-actions-sidebar').find_all('a', class_='button--primary', text='View determination')
            self.assertEqual(len(buttons), 1)

        # Phase: accepted
        submission = ApplicationSubmissionFactory(status='accepted', user=self.applicant, reviewers=[self.user])
        DeterminationFactory(submission=submission, accepted=True, submitted=True)
        assert_view_determination_displayed(submission)

        # Phase: rejected
        submission = ApplicationSubmissionFactory(status='rejected', user=self.applicant, reviewers=[self.user])
        DeterminationFactory(submission=submission, rejected=True, submitted=True)
        assert_view_determination_displayed(submission)

    def test_cant_see_view_determination_primary_action(self):
        def assert_view_determination_not_displayed(submission):
            response = self.get_page(submission)
            buttons = BeautifulSoup(response.content, 'html5lib').find(class_='sidebar').find_all('a', class_='button--primary', text='View determination')
            self.assertEqual(len(buttons), 0)

        # Phase: received / in_discussion
        submission = ApplicationSubmissionFactory(user=self.applicant, reviewers=[self.user])
        assert_view_determination_not_displayed(submission)

        # Phase: ready-for-determination, no determination
        submission.perform_transition('determination', self.user)
        assert_view_determination_not_displayed(submission)

        # Phase: ready-for-determination, draft determination
        DeterminationFactory(submission=submission, author=self.user, accepted=True, submitted=False)
        assert_view_determination_not_displayed(submission)

    def test_can_access_any_submission(self):
        """
        Reviewer settings are being used with default values.
        """
        submission = ApplicationSubmissionFactory(user=self.applicant)
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 200)

    def test_can_only_access_reviewed_submission(self):
        self.reviewer_settings.submission = 'reviewed'
        self.reviewer_settings.state = 'all'
        self.reviewer_settings.outcome = 'all'
        self.reviewer_settings.save()
        submission = ApplicationSubmissionFactory(user=self.applicant, reviewers=[self.user])
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 403)

        ReviewFactory(submission=submission, author__reviewer=self.user, is_draft=False)
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 200)

    def test_can_only_access_external_review_or_higher_submission(self):
        self.reviewer_settings.submission = 'all'
        self.reviewer_settings.state = 'ext_state_or_higher'
        self.reviewer_settings.outcome = 'all'
        self.reviewer_settings.assigned = False
        self.reviewer_settings.save()

        submission = ApplicationSubmissionFactory(user=self.applicant)
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 403)

        submission = ApplicationSubmissionFactory(with_external_review=True, user=self.applicant)
        submission.perform_transition('ext_internal_review', self.user)
        submission.perform_transition('ext_post_review_discussion', self.user)
        submission.perform_transition('ext_external_review', self.user)
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 200)

    def test_cant_access_dismissed_submission(self):
        self.reviewer_settings.submission = 'all'
        self.reviewer_settings.state = 'all'
        self.reviewer_settings.outcome = 'all'
        self.reviewer_settings.assigned = False
        self.reviewer_settings.save()

        submission = ApplicationSubmissionFactory(status='rejected', user=self.applicant)
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 200)

        self.reviewer_settings.outcome = 'all_except_dismissed'
        self.reviewer_settings.save()
        submission = ApplicationSubmissionFactory(status='rejected', user=self.applicant)
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 403)

    def test_can_only_access_accepted_submission(self):
        self.reviewer_settings.submission = 'all'
        self.reviewer_settings.state = 'all'
        self.reviewer_settings.save()

        submission = ApplicationSubmissionFactory(status='rejected', user=self.applicant)
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 200)

        self.reviewer_settings.outcome = 'accepted'
        self.reviewer_settings.save()
        submission = ApplicationSubmissionFactory(status='rejected', user=self.applicant)
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 403)

        submission = ApplicationSubmissionFactory(status='accepted', user=self.applicant)
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 200)

    def test_can_only_access_assigned_submission(self):
        self.reviewer_settings.submission = 'all'
        self.reviewer_settings.state = 'all'
        self.reviewer_settings.outcome = 'all'
        self.reviewer_settings.save()

        submission = ApplicationSubmissionFactory(status='accepted', user=self.applicant)
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 200)

        self.reviewer_settings.assigned = True
        self.reviewer_settings.save()

        submission = ApplicationSubmissionFactory(status='accepted', user=self.applicant)
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 403)

        submission = ApplicationSubmissionFactory(status='accepted', user=self.applicant, reviewers=[self.user])
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 200)


class TestApplicantSubmissionView(BaseSubmissionViewTestCase):
    user_factory = ApplicantFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.submission = ApplicationSubmissionFactory(user=cls.user)
        cls.draft_proposal_submission = InvitedToProposalFactory(user=cls.user, draft=True)

    def __setUp__(self):
        self.refresh(self.submission)
        self.refresh(self.draft_proposal_submission)

    def test_can_view_own_submission(self):
        response = self.get_page(self.submission)
        self.assertContains(response, self.submission.title)

    def test_sees_latest_draft_if_it_exists(self):
        draft_revision = ApplicationRevisionFactory(submission=self.submission)
        self.submission.draft_revision = draft_revision
        self.submission.save()

        draft_submission = self.submission.from_draft()
        response = self.get_page(self.submission)

        self.assertContains(response, draft_submission.title)

    def test_cant_view_others_submission(self):
        submission = ApplicationSubmissionFactory()
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 403)

    def test_get_edit_link_when_editable(self):
        submission = ApplicationSubmissionFactory(user=self.user, status='more_info')
        response = self.get_page(submission)
        self.assertContains(response, 'Edit')
        self.assertContains(response, self.url(submission, 'edit', absolute=False))
        self.assertNotContains(response, 'Congratulations')

    def test_get_congratulations_draft_proposal(self):
        response = self.get_page(self.draft_proposal_submission)
        self.assertContains(response, 'Congratulations')

    def test_can_edit_own_submission(self):
        response = self.get_page(self.draft_proposal_submission, 'edit')
        self.assertContains(response, self.draft_proposal_submission.title)

    def test_can_submit_submission(self):
        old_status = self.draft_proposal_submission.status

        data = prepare_form_data(self.draft_proposal_submission, title='This is different')

        response = self.post_page(self.draft_proposal_submission, {'submit': True, **data}, 'edit')

        url = self.url_from_pattern('funds:submissions:detail', kwargs={'pk': self.draft_proposal_submission.id})

        self.assertRedirects(response, url)
        submission = self.refresh(self.draft_proposal_submission)
        self.assertNotEqual(old_status, submission.status)

    def test_gets_draft_on_edit_submission(self):
        draft_revision = ApplicationRevisionFactory(submission=self.draft_proposal_submission)
        self.draft_proposal_submission.draft_revision = draft_revision
        self.draft_proposal_submission.save()

        response = self.get_page(self.draft_proposal_submission, 'edit')
        self.assertDictEqual(response.context['object'].form_data, draft_revision.form_data)

    def test_cant_edit_submission_incorrect_state(self):
        submission = InvitedToProposalFactory(user=self.user)
        response = self.get_page(submission, 'edit')
        self.assertEqual(response.status_code, 403)

    def test_cant_edit_other_submission(self):
        submission = InvitedToProposalFactory(draft=True)
        response = self.get_page(submission, 'edit')
        self.assertEqual(response.status_code, 403)

    def test_cant_screen_submission(self):
        """
        Test that an applicant cannot set the screening status
        and that they don't see the screening status form.
        """
        screening_outcome = ScreeningStatusFactory()
        response = self.post_page(self.submission, {'form-submitted-screening_form': '', 'screening_statuses': [screening_outcome.id]})
        self.assertNotIn('screening_form', response.context_data)
        submission = self.refresh(self.submission)
        self.assertNotIn(screening_outcome, submission.screening_statuses.all())

    def test_cant_see_screening_status_block(self):
        response = self.get_page(self.submission)
        self.assertNotContains(response, 'Screening status')

    def test_cant_see_add_determination_primary_action(self):
        def assert_add_determination_not_displayed(submission, button_text):
            response = self.get_page(submission)
            # Ignore whitespace (including line breaks) in button text
            pattern = re.compile(rf'\s*{button_text}\s*')
            buttons = BeautifulSoup(response.content, 'html5lib').find_all('a', class_='button--primary', text=pattern)
            self.assertEqual(len(buttons), 0)

        submission = ApplicationSubmissionFactory(status='determination', user=self.user)

        # Phase: ready-for-determination, no determination
        # "Add determination" should not be displayed
        # "Complete draft determination" should not be displayed
        assert_add_determination_not_displayed(submission, 'Add determination')
        assert_add_determination_not_displayed(submission, 'Complete draft determination')

        # Phase: ready-for-determination, draft determination
        # "Add determination" should not be displayed
        # "Complete draft determination" should not be displayed
        DeterminationFactory(submission=submission, accepted=True, submitted=False)
        assert_add_determination_not_displayed(submission, 'Add determination')
        assert_add_determination_not_displayed(submission, 'Complete draft determination')

    def test_cant_see_create_review_primary_action(self):
        def assert_create_review_not_displayed(submission):
            response = self.get_page(submission)
            # Ignore whitespace (including line breaks) in button text
            pattern = re.compile(r'\s*Add a review\s*')
            buttons = BeautifulSoup(response.content, 'html5lib').find_all('a', class_='button--primary', text=pattern)
            self.assertEqual(len(buttons), 0)

        submission = ApplicationSubmissionFactory(user=self.user)

        # Phase: received / in_discussion
        # "Add a review" should not be displayed
        assert_create_review_not_displayed(submission)

        # Phase: internal_review
        # "Add a review" should not be displayed
        staff_user = StaffFactory()
        submission.perform_transition('internal_review', staff_user)
        assert_create_review_not_displayed(submission)

    def test_cant_see_assign_reviewers_primary_action(self):
        submission = ApplicationSubmissionFactory(status='internal_review', user=self.user)
        ReviewerRoleFactory()
        response = self.get_page(submission)
        buttons = BeautifulSoup(response.content, 'html5lib').find(class_='sidebar').find_all('a', class_='button--primary', text='Assign reviewers')
        self.assertEqual(len(buttons), 0)

    def test_cant_see_assign_reviewers_secondary_action(self):
        submission = ApplicationSubmissionFactory(status='internal_review', user=self.user)
        ReviewerRoleFactory()
        response = self.get_page(submission)
        buttons = BeautifulSoup(response.content, 'html5lib').find(class_='sidebar').find_all('a', class_='button--white', text='Reviewers')
        self.assertEqual(len(buttons), 0)

    def test_can_see_view_determination_primary_action(self):
        def assert_view_determination_displayed(submission):
            response = self.get_page(submission)
            buttons = BeautifulSoup(response.content, 'html5lib').find(class_='js-actions-sidebar').find_all('a', class_='button--primary', text='View determination')
            self.assertEqual(len(buttons), 1)

        # Phase: accepted
        submission = ApplicationSubmissionFactory(status='accepted', user=self.user)
        DeterminationFactory(submission=submission, accepted=True, submitted=True)
        assert_view_determination_displayed(submission)

        # Phase: rejected
        submission = ApplicationSubmissionFactory(status='rejected', user=self.user)
        DeterminationFactory(submission=submission, rejected=True, submitted=True)
        assert_view_determination_displayed(submission)

    def test_cant_see_view_determination_primary_action(self):
        def assert_view_determination_not_displayed(submission):
            response = self.get_page(submission)
            buttons = BeautifulSoup(response.content, 'html5lib').find(class_='sidebar').find_all('a', class_='button--primary', text='View determination')
            self.assertEqual(len(buttons), 0)

        # Phase: received / in_discussion
        submission = ApplicationSubmissionFactory(user=self.user)
        assert_view_determination_not_displayed(submission)

        # Phase: ready-for-determination, no determination
        submission.perform_transition('determination', self.user)
        assert_view_determination_not_displayed(submission)

        # Phase: ready-for-determination, draft determination
        DeterminationFactory(submission=submission, accepted=True, submitted=False)
        assert_view_determination_not_displayed(submission)


class TestRevisionsView(BaseSubmissionViewTestCase):
    user_factory = ApplicantFactory

    def test_create_revisions_on_submit(self):
        submission = ApplicationSubmissionFactory(status='draft_proposal', workflow_stages=2, user=self.user)
        old_data = submission.form_data.copy()

        new_title = 'New title'
        new_data = prepare_form_data(submission, title=new_title)

        self.post_page(submission, {'submit': True, **new_data}, 'edit')

        submission = self.refresh(submission)

        self.maxDiff = None
        self.assertEqual(submission.status, 'proposal_discussion')
        self.assertEqual(submission.revisions.count(), 2)
        self.assertDictEqual(submission.revisions.last().form_data, old_data)
        self.assertDictEqual(submission.live_revision.form_data, submission.form_data)
        self.assertEqual(submission.live_revision.author, self.user)
        self.assertEqual(submission.title, new_title)

    def test_dont_update_live_revision_on_save(self):
        submission = ApplicationSubmissionFactory(status='draft_proposal', workflow_stages=2, user=self.user)
        old_data = submission.form_data.copy()

        new_data = prepare_form_data(submission, title='New title')

        self.post_page(submission, {'save': True, **new_data}, 'edit')

        submission = self.refresh(submission)

        self.maxDiff = None
        self.assertEqual(submission.status, 'draft_proposal')
        self.assertEqual(submission.revisions.count(), 2)
        self.assertDictEqual(submission.draft_revision.form_data, submission.from_draft().form_data)
        self.assertEqual(submission.draft_revision.author, self.user)
        self.assertDictEqual(submission.live_revision.form_data, old_data)

    def test_existing_draft_edit_and_submit(self):
        submission = ApplicationSubmissionFactory(status='draft_proposal', workflow_stages=2, user=self.user)
        draft_data = prepare_form_data(submission, title='A new title')

        self.post_page(submission, {'save': True, **draft_data}, 'edit')

        submission = self.refresh(submission)

        newer_title = 'Newer title'
        draft_data = prepare_form_data(submission, title=newer_title)
        self.post_page(submission, {'submit': True, **draft_data}, 'edit')

        submission = self.refresh(submission)

        self.maxDiff = None
        self.assertDictEqual(submission.draft_revision.form_data, submission.from_draft().form_data)
        self.assertDictEqual(submission.live_revision.form_data, submission.form_data)
        self.assertEqual(submission.revisions.count(), 2)

        self.assertEqual(submission.title, newer_title)


class TestRevisionCompare(BaseSubmissionViewTestCase):
    base_view_name = 'revisions:compare'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {
            'submission_pk': instance.pk,
            'to': instance.live_revision.id,
            'from': instance.revisions.last().id,
        }

    def test_renders_with_all_the_diffs(self):
        submission = ApplicationSubmissionFactory()
        new_data = ApplicationSubmissionFactory(round=submission.round, form_fields=submission.form_fields).form_data

        submission.form_data = new_data

        submission.create_revision()

        response = self.get_page(submission)
        self.assertEqual(response.status_code, 200)


class TestRevisionList(BaseSubmissionViewTestCase):
    base_view_name = 'revisions:list'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {'submission_pk': instance.pk}

    def test_list_doesnt_include_draft(self):
        submission = ApplicationSubmissionFactory()
        draft_revision = ApplicationRevisionFactory(submission=submission)
        submission.draft_revision = draft_revision
        submission.save()

        response = self.get_page(submission)

        self.assertNotIn(draft_revision, response.context['object_list'])

    def test_get_in_correct_order(self):
        submission = ApplicationSubmissionFactory()

        revision = ApplicationRevisionFactory(submission=submission)
        ApplicationRevision.objects.filter(id=revision.id).update(timestamp=timezone.now() - timedelta(days=1))

        revision_older = ApplicationRevisionFactory(submission=submission)
        ApplicationRevision.objects.filter(id=revision_older.id).update(timestamp=timezone.now() - timedelta(days=2))

        response = self.get_page(submission)

        self.assertSequenceEqual(
            response.context['object_list'],
            [submission.live_revision, revision, revision_older],
        )


class TestStaffSealedView(BaseSubmissionViewTestCase):
    user_factory = StaffFactory

    def test_redirected_to_sealed(self):
        submission = SealedSubmissionFactory()
        response = self.get_page(submission)
        url = self.url_from_pattern('funds:submissions:sealed', kwargs={'pk': submission.id})
        self.assertRedirects(response, url)

    def test_cant_post_to_sealed(self):
        submission = SealedSubmissionFactory()
        response = self.post_page(submission, {'some': 'data'}, 'sealed')
        # Because of the redirect chain the url returned is not absolute
        url = self.url_from_pattern('funds:submissions:sealed', kwargs={'pk': submission.id}, absolute=False)
        self.assertRedirects(response, url)

    def test_non_sealed_unaffected(self):
        submission = ApplicationSubmissionFactory()
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 200)

    def test_non_sealed_redirected_away(self):
        submission = ApplicationSubmissionFactory()
        response = self.get_page(submission, 'sealed')
        url = self.url_from_pattern('funds:submissions:detail', kwargs={'pk': submission.id})
        self.assertRedirects(response, url)


class TestSuperUserSealedView(BaseSubmissionViewTestCase):
    user_factory = SuperUserFactory

    def test_redirected_to_sealed(self):
        submission = SealedSubmissionFactory()
        response = self.get_page(submission)
        url = self.url_from_pattern('funds:submissions:sealed', kwargs={'pk': submission.id})
        self.assertRedirects(response, url)

    def test_can_post_to_sealed(self):
        submission = SealedSubmissionFactory()
        response = self.post_page(submission, {}, 'sealed')
        url = self.url_from_pattern('funds:submissions:detail', kwargs={'pk': submission.id})
        self.assertRedirects(response, url)

    def test_peeking_is_logged(self):
        submission = SealedSubmissionFactory()
        self.post_page(submission, {}, 'sealed')

        self.assertTrue('peeked' in self.client.session)
        self.assertTrue(str(submission.id) in self.client.session['peeked'])
        self.assertEqual(Activity.objects.count(), 1)
        self.assertTrue('sealed' in Activity.objects.first().message)

    def test_not_asked_again(self):
        submission = SealedSubmissionFactory()

        self.post_page(submission, {}, 'sealed')

        # Now request the page again
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 200)

    def test_can_view_multiple_sealed(self):
        sealed_round = SealedRoundFactory()
        first, second = SealedSubmissionFactory.create_batch(2, round=sealed_round)

        self.post_page(first, {}, 'sealed')
        self.post_page(second, {}, 'sealed')

        self.assertTrue('peeked' in self.client.session)
        self.assertTrue(str(first.id) in self.client.session['peeked'])
        self.assertTrue(str(second.id) in self.client.session['peeked'])


class TestSuperUserSubmissionView(BaseSubmissionViewTestCase):
    user_factory = SuperUserFactory

    @classmethod
    def setUpTestData(cls):
        cls.submission = ApplicationSubmissionFactory()
        super().setUpTestData()

    def __setUp__(self):
        self.refresh(self.submission)

    def test_can_screen_submission(self):
        ScreeningStatus.objects.all().delete()
        screening_outcome1 = ScreeningStatusFactory()
        screening_outcome1.yes = True
        screening_outcome1.save()
        screening_outcome2 = ScreeningStatusFactory()
        screening_outcome2.yes = True
        screening_outcome2.default = True
        screening_outcome2.save()
        self.submission.screening_statuses.clear()
        self.submission.screening_statuses.add(screening_outcome2)
        self.post_page(self.submission, {'form-submitted-screening_form': '', 'screening_statuses': [screening_outcome1.id, screening_outcome2.id]})
        submission = self.refresh(self.submission)
        self.assertEqual(submission.screening_statuses.count(), 2)

    def test_can_screen_applications_in_final_status(self):
        """
        Now that the submission has been rejected (final determination),
        we can still screen it because we are super user
        """
        submission = ApplicationSubmissionFactory(rejected=True)
        ScreeningStatus.objects.all().delete()
        screening_outcome1 = ScreeningStatusFactory()
        screening_outcome1.yes = True
        screening_outcome1.save()
        screening_outcome2 = ScreeningStatusFactory()
        screening_outcome2.yes = True
        screening_outcome2.default = True
        screening_outcome2.save()
        submission.screening_statuses.add(screening_outcome2)
        response = self.post_page(submission, {'form-submitted-screening_form': '', 'screening_statuses': [screening_outcome1.id, screening_outcome2.id]})
        submission = self.refresh(submission)
        self.assertEqual(response.context_data['screening_form'].should_show, True)
        self.assertEqual(submission.screening_statuses.count(), 2)

        # Check that an activity was created that should only be viewable internally
        activity = Activity.objects.filter(message__contains='Screening status').first()
        self.assertEqual(activity.visibility, TEAM)


class TestSubmissionDetailSimplifiedView(TestCase):
    def test_staff_only(self):
        factory = RequestFactory()
        submission = ApplicationSubmissionFactory()
        ProjectFactory(submission=submission)

        request = factory.get(f'/submission/{submission.pk}')
        request.user = StaffFactory()

        response = SubmissionDetailSimplifiedView.as_view()(request, pk=submission.pk)
        self.assertEqual(response.status_code, 200)

        request.user = ApplicantFactory()
        with self.assertRaises(PermissionDenied):
            SubmissionDetailSimplifiedView.as_view()(request, pk=submission.pk)

    def test_project_required(self):
        factory = RequestFactory()
        submission = ApplicationSubmissionFactory()

        request = factory.get(f'/submission/{submission.pk}')
        request.user = StaffFactory()

        with self.assertRaises(Http404):
            SubmissionDetailSimplifiedView.as_view()(request, pk=submission.pk)

        ProjectFactory(submission=submission)
        response = SubmissionDetailSimplifiedView.as_view()(request, pk=submission.pk)
        self.assertEqual(response.status_code, 200)


class BaseSubmissionFileViewTestCase(BaseViewTestCase):
    url_name = 'funds:submissions:{}'
    base_view_name = 'serve_private_media'

    def get_kwargs(self, instance):
        document_fields = list(instance.file_field_ids)
        field_id = document_fields[0]
        document = instance.data(field_id)
        return {
            'pk': instance.pk,
            'field_id': field_id,
            'file_name': document.basename,
        }


class TestStaffSubmissionFileView(BaseSubmissionFileViewTestCase):
    user_factory = StaffFactory

    def test_staff_can_access(self):
        submission = ApplicationSubmissionFactory()
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [])


class TestUserSubmissionFileView(BaseSubmissionFileViewTestCase):
    user_factory = ApplicantFactory

    def test_owner_can_access(self):
        submission = ApplicationSubmissionFactory(user=self.user)
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [])

    def test_user_can_not_access(self):
        submission = ApplicationSubmissionFactory()
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.redirect_chain, [])


class TestAnonSubmissionFileView(BaseSubmissionFileViewTestCase):
    user_factory = AnonymousUser

    def test_anonymous_can_not_access(self):
        submission = ApplicationSubmissionFactory()
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 2)
        for path, _ in response.redirect_chain:
            self.assertIn(reverse('users_public:login'), path)


class BaseProjectDeleteTestCase(BaseViewTestCase):
    url_name = 'funds:submissions:reminders:{}'
    base_view_name = 'delete'

    def get_kwargs(self, instance):
        return {'pk': instance.id, 'submission_pk': instance.submission.id}


class TestStaffReminderDeleteView(BaseProjectDeleteTestCase):
    user_factory = StaffFactory

    def test_has_access(self):
        reminder = ReminderFactory()
        response = self.get_page(reminder)
        self.assertEqual(response.status_code, 200)

    def test_confirm_message(self):
        reminder = ReminderFactory()
        response = self.get_page(reminder)
        self.assertContains(response, 'Are you sure you want to delete')
        self.assertEqual(response.status_code, 200)


class TestUserReminderDeleteView(BaseProjectDeleteTestCase):
    user_factory = ApplicantFactory

    def test_doesnt_has_access(self):
        reminder = ReminderFactory()
        response = self.get_page(reminder)
        self.assertEqual(response.status_code, 403)


@override_settings(ROOT_URLCONF='hypha.apply.urls')
class TestReviewerLeaderboard(TestCase):
    def test_applicant_cannot_access_reviewer_leaderboard(self):
        self.client.force_login(ApplicantFactory())
        response = self.client.get('/apply/submissions/reviews/', follow=True, secure=True)
        self.assertEqual(response.status_code, 403)

    def test_community_reviewer_cannot_access_reviewer_leaderboard(self):
        self.client.force_login(CommunityReviewerFactory())
        response = self.client.get('/apply/submissions/reviews/', follow=True, secure=True)
        self.assertEqual(response.status_code, 403)

    def test_partner_cannot_access_reviewer_leaderboard(self):
        self.client.force_login(PartnerFactory())
        response = self.client.get('/apply/submissions/reviews/', follow=True, secure=True)
        self.assertEqual(response.status_code, 403)

    def test_reviewer_cannot_access_leader_board(self):
        self.client.force_login(ReviewerFactory())
        response = self.client.get('/apply/submissions/reviews/', follow=True, secure=True)
        self.assertEqual(response.status_code, 403)

    def test_staff_can_access_leaderboard(self):
        self.client.force_login(StaffFactory())
        response = self.client.get('/apply/submissions/reviews/', follow=True, secure=True)
        self.assertEqual(response.status_code, 200)


class TestUpdateReviewersMixin(BaseSubmissionViewTestCase):
    user_factory = StaffFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.staff = StaffFactory.create_batch(4)
        cls.reviewers = ReviewerFactory.create_batch(4)
        cls.roles = ReviewerRoleFactory.create_batch(2)

    def post_form(self, submission, reviewer_roles=list(), reviewers=list()):
        data = {
            'form-submitted-reviewer_form': '',
            'reviewer_reviewers': [r.id for r in reviewers]
        }
        data.update(
            **{
                f'role_reviewer_{slugify(str(role))}': reviewer.id
                for role, reviewer in zip(self.roles, reviewer_roles)
            }
        )
        return self.post_page(submission, data)

    def test_submission_transition_all_reviewer_roles_not_assigned(self):
        submission = ApplicationSubmissionFactory(lead=self.user, status=INITIAL_STATE)
        self.post_form(submission, reviewer_roles=[self.staff[0]])
        submission = ApplicationSubmission.objects.get(id=submission.id)

        # Submission state shouldn't change when all_reviewer_roles_not_assigned
        self.assertEqual(
            submission.status,
            INITIAL_STATE
        )

    def test_submission_transition_to_internal_review(self):
        submission = ApplicationSubmissionFactory(lead=self.user, status=INITIAL_STATE)
        self.post_form(submission, reviewer_roles=[self.staff[0], self.staff[1]])
        submission = ApplicationSubmission.objects.get(id=submission.id)

        # Automatically transition the application to "Internal review".
        self.assertEqual(
            submission.status,
            submission.workflow.stepped_phases[2][0].name
        )

    def test_submission_transition_to_proposal_internal_review(self):
        submission = ApplicationSubmissionFactory(lead=self.user, status='proposal_discussion', workflow_stages=2)
        self.post_form(submission, reviewer_roles=[self.staff[0], self.staff[1]])
        submission = ApplicationSubmission.objects.get(id=submission.id)

        # Automatically transition the application to "Internal review".
        self.assertEqual(
            submission.status,
            'proposal_internal_review'
        )
