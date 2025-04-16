import factory
from dateutil.relativedelta import relativedelta
from django.utils import timezone

from hypha.apply.stream_forms.testing.factories import (
    FormDataFactory,
    NonFileFormFieldsBlockFactory,
)

from ..models import Report, ReportConfig, ReportVersion


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


class ReportDataFactory(FormDataFactory):
    field_factory = NonFileFormFieldsBlockFactory


class ReportVersionFactory(factory.django.DjangoModelFactory):
    report = factory.SubFactory(
        "hypha.apply.projects.reports.tests.factories.ReportFactory"
    )
    submitted = factory.LazyFunction(timezone.now)
    form_data = factory.SubFactory(
        ReportDataFactory,
        form_fields=factory.SelfAttribute("..report.form_fields"),
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
    form_fields = NonFileFormFieldsBlockFactory
    # TODO: is it better to keep the following link between form_data and form_fields or to remove it?
    form_data = factory.SubFactory(
        ReportDataFactory,
        form_fields=factory.SelfAttribute("..form_fields"),
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
