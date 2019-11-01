import datetime

import factory
import wagtail_factories

from opentech.apply.funds.models import (
    ApplicationSubmission,
    ApplicationRevision,
    AssignedReviewers,
    FundType,
    LabType,
    RequestForPartners,
    ReviewerRole,
    Round,
    ScreeningStatus,
    SealedRound,
)
from opentech.apply.funds.models.forms import (
    ApplicationForm,
    ApplicationBaseForm,
    ApplicationBaseReviewForm,
    LabBaseForm,
    LabBaseReviewForm,
    RoundBaseForm,
    RoundBaseReviewForm,
)
from opentech.apply.funds.workflow import ConceptProposal, Request
from opentech.apply.home.factories import ApplyHomePageFactory
from opentech.apply.stream_forms.testing.factories import FormDataFactory
from opentech.apply.users.groups import STAFF_GROUP_NAME, REVIEWER_GROUP_NAME
from opentech.apply.users.tests.factories import StaffFactory, ApplicantFactory, GroupFactory

from . import blocks


__all__ = [
    'FundTypeFactory',
    'ApplicationBaseFormFactory',
    'ApplicationFormFactory',
    'ApplicationRevisionFactory',
    'ApplicationSubmissionFactory',
    'AssignedReviewersFactory',
    'AssignedWithRoleReviewersFactory',
    'InvitedToProposalFactory',
    'RoundFactory',
    'RoundBaseFormFactory',
    'LabFactory',
    'LabBaseFormFactory',
    'LabSubmissionFactory',
    'RequestForPartnersFactory',
    'ScreeningStatusFactory',
    'SealedRoundFactory',
    'SealedSubmissionFactory',
    'ReviewerRoleFactory',
    'TodayRoundFactory',
    'workflow_for_stages',
]


def workflow_for_stages(stages):
    return {
        1: Request.admin_name,
        2: ConceptProposal.admin_name,
    }[stages]


class AbstractApplicationFactory(wagtail_factories.PageFactory):
    class Meta:
        abstract = True

    class Params:
        workflow_stages = 1

    title = factory.Faker('sentence')
    parent = factory.SubFactory(ApplyHomePageFactory)

    # Will need to update how the stages are identified as Fund Page changes
    workflow_name = factory.LazyAttribute(lambda o: workflow_for_stages(o.workflow_stages))
    approval_form = factory.SubFactory('opentech.apply.projects.tests.factories.ProjectApprovalFormFactory')

    @factory.post_generation
    def forms(self, create, extracted, **kwargs):
        if create:
            for index, _ in enumerate(self.workflow.stages, 1):
                # Generate a form based on all defined fields on the model
                ApplicationBaseFormFactory(
                    application=self,
                    stage=index,
                    **kwargs,
                )
                ApplicationBaseReviewForm(
                    application=self,
                    **kwargs,
                )


class FundTypeFactory(AbstractApplicationFactory):
    class Meta:
        model = FundType


class RequestForPartnersFactory(AbstractApplicationFactory):
    class Meta:
        model = RequestForPartners


class AbstractRelatedFormFactory(factory.DjangoModelFactory):
    class Meta:
        abstract = True
    form = factory.SubFactory('opentech.apply.funds.tests.factories.ApplicationFormFactory')


class ApplicationBaseFormFactory(AbstractRelatedFormFactory):
    class Meta:
        model = ApplicationBaseForm
    application = factory.SubFactory(FundTypeFactory)


class ApplicationFormFactory(factory.DjangoModelFactory):
    class Meta:
        model = ApplicationForm

    name = factory.Faker('word')
    form_fields = blocks.CustomFormFieldsFactory


class RoundFactory(wagtail_factories.PageFactory):
    class Meta:
        model = Round

    class Params:
        now = factory.Trait(
            start_date=factory.LazyFunction(datetime.date.today),
            end_date=factory.LazyFunction(lambda: datetime.date.today() + datetime.timedelta(days=7)),
        )
        closed = factory.Trait(
            start_date=factory.LazyFunction(lambda: datetime.date.today() - datetime.timedelta(days=7)),
            end_date=factory.LazyFunction(lambda: datetime.date.today() - datetime.timedelta(days=1)),
        )

    title = factory.Sequence('Round {}'.format)
    start_date = factory.Sequence(lambda n: datetime.date.today() + datetime.timedelta(days=7 * n + 1))
    end_date = factory.Sequence(lambda n: datetime.date.today() + datetime.timedelta(days=7 * (n + 1)))
    lead = factory.SubFactory(StaffFactory)
    parent = factory.SubFactory(FundTypeFactory)

    @factory.post_generation
    def forms(self, create, extracted, **kwargs):
        if create:
            for index, _ in enumerate(self.workflow.stages, 1):
                # Generate a form based on all defined fields on the model
                RoundBaseFormFactory(
                    round=self,
                    stage=index,
                    **kwargs,
                )
                RoundBaseReviewFormFactory(
                    round=self,
                    **kwargs,
                )


class SealedRoundFactory(RoundFactory):
    class Meta:
        model = SealedRound


class TodayRoundFactory(RoundFactory):
    start_date = factory.LazyFunction(datetime.date.today)
    end_date = factory.LazyFunction(lambda: datetime.date.today() + datetime.timedelta(days=7))


class RoundBaseFormFactory(AbstractRelatedFormFactory):
    class Meta:
        model = RoundBaseForm
    round = factory.SubFactory(RoundFactory)


class LabFactory(AbstractApplicationFactory):
    class Meta:
        model = LabType

    lead = factory.SubFactory(StaffFactory)

    @factory.post_generation
    def forms(self, create, extracted, **kwargs):
        if create:
            for index, _ in enumerate(self.workflow.stages, 1):
                # Generate a form based on all defined fields on the model
                LabBaseFormFactory(
                    lab=self,
                    stage=index,
                    **kwargs,
                )
                LabBaseReviewFormFactory(
                    lab=self,
                    **kwargs,
                )


class LabBaseFormFactory(AbstractRelatedFormFactory):
    class Meta:
        model = LabBaseForm
    lab = factory.SubFactory(LabFactory)


class ApplicationFormDataFactory(FormDataFactory):
    field_factory = blocks.CustomFormFieldsFactory


class ApplicationSubmissionFactory(factory.DjangoModelFactory):
    class Meta:
        model = ApplicationSubmission

    class Params:
        workflow_stages = 1
        rejected = factory.Trait(
            status='rejected'
        )

    form_fields = blocks.CustomFormFieldsFactory
    form_data = factory.SubFactory(
        ApplicationFormDataFactory,
        form_fields=factory.SelfAttribute('..form_fields'),
    )
    page = factory.SelfAttribute('.round.fund')
    workflow_name = factory.LazyAttribute(lambda o: workflow_for_stages(o.workflow_stages))
    round = factory.SubFactory(
        RoundFactory,
        workflow_name=factory.SelfAttribute('..workflow_name'),
        lead=factory.SelfAttribute('..lead'),
    )
    user = factory.SubFactory(ApplicantFactory)
    lead = factory.SubFactory(StaffFactory)
    live_revision = None
    draft_revision = None

    @factory.post_generation
    def reviewers(self, create, reviewers, **kwargs):
        if create and reviewers:
            for reviewer in reviewers:
                AssignedReviewers.objects.get_or_create_for_user(
                    reviewer=reviewer,
                    submission=self,
                )


class ReviewerRoleFactory(factory.DjangoModelFactory):
    class Meta:
        model = ReviewerRole

    name = factory.Faker('word')
    order = factory.Sequence(lambda n: n)


class AssignedReviewersFactory(factory.DjangoModelFactory):
    class Meta:
        model = AssignedReviewers
        django_get_or_create = ('submission', 'reviewer')

    class Params:
        staff = factory.Trait(type=factory.SubFactory(GroupFactory, name=STAFF_GROUP_NAME))

    submission = factory.SubFactory(ApplicationSubmissionFactory)
    role = None
    reviewer = factory.SubFactory(StaffFactory)
    type = factory.SubFactory(GroupFactory, name=REVIEWER_GROUP_NAME)


class AssignedWithRoleReviewersFactory(AssignedReviewersFactory):
    role = factory.SubFactory(ReviewerRoleFactory)


class InvitedToProposalFactory(ApplicationSubmissionFactory):
    class Params:
        workflow_stages = 2
        draft = factory.Trait(
            status='draft_proposal',
        )

    status = 'proposal_discussion'
    previous = factory.RelatedFactory(
        ApplicationSubmissionFactory,
        'next',
        round=factory.SelfAttribute('..round'),
        page=factory.SelfAttribute('..page'),
        status='invited_to_proposal',
    )


class SealedSubmissionFactory(ApplicationSubmissionFactory):
    page = factory.SubFactory(RequestForPartnersFactory)
    round = factory.SubFactory(
        SealedRoundFactory,
        workflow_name=factory.SelfAttribute('..workflow_name'),
        lead=factory.SelfAttribute('..lead'),
        now=True,
    )


class LabSubmissionFactory(ApplicationSubmissionFactory):
    round = None
    page = factory.SubFactory(LabFactory)


class ApplicationRevisionFactory(factory.DjangoModelFactory):
    class Meta:
        model = ApplicationRevision

    submission = factory.SubFactory('opentech.apply.funds.tests.factories.ApplicationSubmissionFactory')
    form_data = factory.SubFactory(
        ApplicationFormDataFactory,
        form_fields=factory.SelfAttribute('..submission.form_fields'),
        for_factory=ApplicationSubmissionFactory,
        clean=True,
    )


class AbstractReviewFormFactory(factory.DjangoModelFactory):
    class Meta:
        abstract = True
    form = factory.SubFactory('opentech.apply.review.tests.factories.ReviewFormFactory')


class ApplicationBaseReviewFormFactory(AbstractReviewFormFactory):
    class Meta:
        model = ApplicationBaseReviewForm

    application = factory.SubFactory(FundTypeFactory)


class RoundBaseReviewFormFactory(AbstractReviewFormFactory):
    class Meta:
        model = RoundBaseReviewForm

    round = factory.SubFactory(RoundFactory)


class LabBaseReviewFormFactory(AbstractReviewFormFactory):
    class Meta:
        model = LabBaseReviewForm

    lab = factory.SubFactory(LabFactory)


class ScreeningStatusFactory(factory.DjangoModelFactory):
    class Meta:
        model = ScreeningStatus

    title = factory.Iterator(["Bad", "Good"])
