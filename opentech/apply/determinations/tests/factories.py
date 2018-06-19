import factory

from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory

from ..models import Determination, APPROVED, UNDETERMINED, UNAPPROVED
from ..views import get_form_for_stage


class DeterminationDataFactory(factory.DictFactory):
    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        submission = kwargs.pop('submission')
        form = get_form_for_stage(submission)(request=None, submission=None)
        form_fields = {}
        for field_name, field in form.fields.items():
            form_fields[field_name] = 0

        form_fields.update(**kwargs)
        return super()._build(model_class, *args, **form_fields)


class DeterminationFactory(factory.DjangoModelFactory):
    class Meta:
        model = Determination

    class Params:
        submitted = factory.Trait(determination=APPROVED, is_draft=False)
        approved = factory.Trait(determination=APPROVED)
        rejected = factory.Trait(determination=UNAPPROVED)
        not_draft = factory.Trait(is_draft=False)

    submission = factory.SubFactory(ApplicationSubmissionFactory)
    author = factory.SelfAttribute('submission.lead')

    determination = UNDETERMINED
    determination_message = factory.Faker('sentence')
    determination_data = factory.Dict({'submission': factory.SelfAttribute('..submission')}, dict_factory=DeterminationDataFactory)

    is_draft = True
