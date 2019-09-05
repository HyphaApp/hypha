from datetime import timedelta
import json

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from opentech.apply.activity.models import Activity, TEAM
from opentech.apply.projects.models import Project
from opentech.apply.projects.tests.factories import ProjectFactory
from opentech.apply.determinations.tests.factories import DeterminationFactory
from opentech.apply.funds.tests.factories import (
    ApplicationSubmissionFactory,
    ApplicationRevisionFactory,
    AssignedWithRoleReviewersFactory,
    AssignedReviewersFactory,
    InvitedToProposalFactory,
    LabSubmissionFactory,
    ReviewerRoleFactory,
    ScreeningStatusFactory,
    SealedRoundFactory,
    SealedSubmissionFactory,
)
from opentech.apply.review.tests.factories import ReviewFactory
from opentech.apply.stream_forms.testing.factories import flatten_for_form
from opentech.apply.users.tests.factories import (
    ReviewerFactory,
    StaffFactory,
    SuperUserFactory,
    ApplicantFactory,
)
from opentech.apply.utils.testing import make_request
from opentech.apply.utils.testing.tests import BaseViewTestCase

from ..models import ApplicationRevision, ApplicationSubmission
from ..views import SubmissionDetailSimplifiedView


def prepare_form_data(submission, **kwargs):
    data = submission.raw_data

    for field, value in kwargs.items():
        # convert named fields into  id
        field_id = submission.field(field).id
        data[field_id] = value

    address_field = submission.named_blocks['address']
    address = data.pop(address_field)
    data.update(**prepare_address(address, address_field))

    return data


def prepare_address(address, field):
    address = json.loads(address)
    address['locality'] = {
        'localityname': address.pop('localityname'),
        'administrativearea': address.pop('administrativearea'),
        'postalcode': address.pop('postalcode'),
    }
    address = flatten_for_form(address, field, number=True)
    return address


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
        submission = ApplicationSubmissionFactory(form_fields__exclude__value=True)
        response = self.get_page(submission)
        self.assertNotContains(response, 'Value')

    def test_can_screen_submission(self):
        screening_outcome = ScreeningStatusFactory()
        self.post_page(self.submission, {'form-submitted-screening_form': '', 'screening_status': screening_outcome.id})
        submission = self.refresh(self.submission)
        self.assertEqual(submission.screening_status, screening_outcome)

    def test_can_view_submission_screening_block(self):
        response = self.get_page(self.submission)
        self.assertContains(response, 'Screening Status')

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
        response = self.post_page(self.submission, {'form-submitted-screening_form': '', 'screening_status': screening_outcome.id})
        self.assertNotIn('screening_form', response.context_data)
        submission = self.refresh(self.submission)
        self.assertNotEqual(submission.screening_status, screening_outcome)

    def test_cant_see_screening_status_block(self):
        response = self.get_page(self.submission)
        self.assertNotContains(response, 'Screening Status')


class TestRevisionsView(BaseSubmissionViewTestCase):
    user_factory = ApplicantFactory

    def test_create_revisions_on_submit(self):
        submission = ApplicationSubmissionFactory(status='draft_proposal', workflow_stages=2, user=self.user)
        old_data = submission.form_data.copy()

        new_title = 'New title'
        new_data = prepare_form_data(submission, title=new_title)

        self.post_page(submission, {'submit': True, **new_data}, 'edit')

        submission = self.refresh(submission)

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
        self.assertEqual(submission.revisions.count(), 2)
        self.assertDictEqual(submission.draft_revision.form_data, submission.from_draft().form_data)
        self.assertDictEqual(submission.live_revision.form_data, submission.form_data)

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
        screening_outcome = ScreeningStatusFactory()
        self.post_page(self.submission, {'form-submitted-screening_form': '', 'screening_status': screening_outcome.id})
        submission = self.refresh(self.submission)
        self.assertEqual(submission.screening_status, screening_outcome)

    def test_can_screen_applications_in_final_status(self):
        """
        Now that the submission has been rejected (final determination),
        we can still screen it because we are super user
        """
        submission = ApplicationSubmissionFactory(rejected=True)
        screening_outcome = ScreeningStatusFactory()
        response = self.post_page(submission, {'form-submitted-screening_form': '', 'screening_status': screening_outcome.id})
        submission = self.refresh(submission)
        self.assertEqual(response.context_data['screening_form'].should_show, True)
        self.assertEqual(submission.screening_status, screening_outcome)

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


@override_settings(ROOT_URLCONF='opentech.apply.urls')
class TestSubmissionDetailUnauthenticatedView(TestCase):
    def test_unauthenticated_user_can_access_view(self):
        submission = ApplicationSubmissionFactory(rejected=True)

        url = reverse('funds:submissions:unauthenticated', kwargs={'pk': submission.pk})
        response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 200)
