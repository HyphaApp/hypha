import decimal

import factory
from dateutil.relativedelta import relativedelta
from django.utils import timezone

from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory
from hypha.apply.stream_forms.testing.factories import (
    FormDataFactory,
    FormFieldsBlockFactory,
    NonFileFormFieldsBlockFactory,
)
from hypha.apply.users.groups import APPROVER_GROUP_NAME, STAFF_GROUP_NAME
from hypha.apply.users.tests.factories import GroupFactory, StaffFactory, UserFactory

from ..models.payment import Invoice, InvoiceDeliverable, SupportingDocument
from ..models.project import (
    COMPLETE,
    INVOICING_AND_REPORTING,
    Contract,
    Deliverable,
    DocumentCategory,
    PacketFile,
    PAFApprovals,
    PAFReviewersRole,
    Project,
    ProjectForm,
    ProjectReportForm,
    ProjectSOWForm,
)
from ..models.report import Report, ReportConfig, ReportVersion

ADDRESS = {
    "country": "GB",
    "thoroughfare": factory.Faker("street_name").evaluate(None, None, {"locale": None}),
    "premise": factory.Faker("building_number").evaluate(None, None, {"locale": None}),
    "locality": {
        "localityname": factory.Faker("city").evaluate(None, None, {"locale": None}),
        "administrativearea": factory.Faker("city").evaluate(
            None, None, {"locale": None}
        ),
        "postal_code": "SW1 4AQ",
    },
}


def address_to_form_data():
    """
    Generate a AddressField compatible dictionary from the address data
    """
    return {
        "contact_address_0": ADDRESS["country"],
        "contact_address_1": ADDRESS["thoroughfare"],
        "contact_address_2": ADDRESS["premise"],
        "contact_address_3_0": ADDRESS["locality"]["localityname"],
        "contact_address_3_1": ADDRESS["locality"]["administrativearea"],
        "contact_address_3_2": ADDRESS["locality"]["postal_code"],
    }


class DocumentCategoryFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence("name {}".format)
    recommended_minimum = 1

    class Meta:
        model = DocumentCategory


class ProjectFormFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProjectForm

    name = factory.Faker("word")
    form_fields = FormFieldsBlockFactory


class ProjectSOWFormFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProjectSOWForm

    name = factory.Faker("word")
    form_fields = FormFieldsBlockFactory


class ProjectFormDataFactory(FormDataFactory):
    field_factory = FormFieldsBlockFactory


class ProjectReportFormFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProjectReportForm

    name = factory.Faker("word")
    form_fields = FormFieldsBlockFactory


class ProjectFactory(factory.django.DjangoModelFactory):
    submission = factory.SubFactory(ApplicationSubmissionFactory)
    user = factory.SubFactory(UserFactory)

    title = factory.Sequence("name {}".format)
    lead = factory.SubFactory(StaffFactory)
    value = decimal.Decimal("100")
    proposed_start = factory.LazyFunction(timezone.now)
    proposed_end = factory.LazyFunction(timezone.now)

    is_locked = False

    form_fields = FormFieldsBlockFactory
    form_data = factory.SubFactory(
        ProjectFormDataFactory,
        form_fields=factory.SelfAttribute("..form_fields"),
    )

    class Meta:
        model = Project

    class Params:
        in_approval = factory.Trait(
            is_locked=True,
        )
        in_progress = factory.Trait(
            status=INVOICING_AND_REPORTING,
        )
        is_complete = factory.Trait(
            status=COMPLETE,
        )


class PAFReviewerRoleFactory(factory.django.DjangoModelFactory):
    label = factory.Faker("name")

    class Meta:
        model = PAFReviewersRole

    @factory.post_generation
    def user_roles(self, create, extracted, **kwargs):
        if create:
            self.user_roles.add(
                GroupFactory(name=STAFF_GROUP_NAME),
                GroupFactory(name=APPROVER_GROUP_NAME),
            )


class PAFApprovalsFactory(factory.django.DjangoModelFactory):
    project = factory.SubFactory(ProjectFactory)
    paf_reviewer_role = factory.SubFactory(PAFReviewerRoleFactory)
    user = factory.SubFactory(StaffFactory)

    class Meta:
        model = PAFApprovals


class ContractFactory(factory.django.DjangoModelFactory):
    approver = factory.SubFactory(StaffFactory)
    project = factory.SubFactory(ProjectFactory)
    approved_at = factory.LazyFunction(timezone.now)
    signed_by_applicant = True

    file = factory.django.FileField()

    class Meta:
        model = Contract


class PacketFileFactory(factory.django.DjangoModelFactory):
    category = factory.SubFactory(DocumentCategoryFactory)
    project = factory.SubFactory(ProjectFactory)

    title = factory.Sequence("name {}".format)
    document = factory.django.FileField()

    class Meta:
        model = PacketFile


class InvoiceFactory(factory.django.DjangoModelFactory):
    invoice_number = factory.Faker("name")
    invoice_amount = decimal.Decimal("10")
    project = factory.SubFactory(ProjectFactory)
    by = factory.SubFactory(UserFactory)
    document = factory.django.FileField()

    class Meta:
        model = Invoice


class SupportingDocumentFactory(factory.django.DjangoModelFactory):
    invoice = factory.SubFactory(InvoiceFactory)

    document = factory.django.FileField()

    class Meta:
        model = SupportingDocument


class ReportConfigFactory(factory.django.DjangoModelFactory):
    project = factory.SubFactory(
        "hypha.apply.projects.tests.factories.ApprovedProjectFactory",
        report_config=None,
    )

    class Meta:
        model = ReportConfig
        django_get_or_create = ("project",)

    class Params:
        weeks = factory.Trait(
            frequency=ReportConfig.WEEK,
        )


class ReportVersionDataFactory(FormDataFactory):
    field_factory = NonFileFormFieldsBlockFactory


class ReportVersionFactory(factory.django.DjangoModelFactory):
    report = factory.SubFactory("hypha.apply.projects.tests.factories.ReportFactory")
    submitted = factory.LazyFunction(timezone.now)
    form_fields = NonFileFormFieldsBlockFactory
    # TODO: is it better to keep the following link between form_data and form_fields or to remove it?
    form_data = factory.SubFactory(
        ReportVersionDataFactory,
        form_fields=factory.SelfAttribute("..form_fields"),
    )
    draft = True

    class Meta:
        model = ReportVersion

    @factory.post_generation
    def relate(obj, create, should_relate, **kwargs):
        if not create:
            return

        if should_relate:
            if obj.draft:
                obj.report.draft = obj
            else:
                obj.report.current = obj
                obj.report.submitted = obj.submitted
            obj.report.save()


class ReportFactory(factory.django.DjangoModelFactory):
    project = factory.SubFactory(
        "hypha.apply.projects.tests.factories.ApprovedProjectFactory"
    )
    end_date = factory.LazyFunction(timezone.now)

    class Meta:
        model = Report

    class Params:
        past_due = factory.Trait(
            end_date=factory.LazyFunction(
                lambda: timezone.now() - relativedelta(days=1)
            )
        )
        is_submitted = factory.Trait(
            version=factory.RelatedFactory(
                ReportVersionFactory, "report", draft=False, relate=True
            )
        )
        is_draft = factory.Trait(
            version=factory.RelatedFactory(ReportVersionFactory, "report", relate=True),
        )


class ApprovedProjectFactory(ProjectFactory):
    contract = factory.RelatedFactory(ContractFactory, "project")
    report_config = factory.RelatedFactory(ReportConfigFactory, "project")


class DeliverableFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence("name {}".format)
    unit_price = decimal.Decimal("100")
    project = factory.SubFactory(ProjectFactory)

    class Meta:
        model = Deliverable


class InvoiceDeliverableFactory(factory.django.DjangoModelFactory):
    deliverable = factory.SubFactory(DeliverableFactory)

    class Meta:
        model = InvoiceDeliverable
