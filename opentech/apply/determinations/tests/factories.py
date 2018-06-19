import factory

from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory

from ..models import Determination, ACCEPTED, NEEDS_MORE_INFO, REJECTED
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
        submitted = factory.Trait(outcome=ACCEPTED, is_draft=False)
        accepted = factory.Trait(outcome=ACCEPTED)
        rejected = factory.Trait(outcome=REJECTED)
        not_draft = factory.Trait(is_draft=False)

    submission = factory.SubFactory(ApplicationSubmissionFactory)
    author = factory.SelfAttribute('submission.lead')

    outcome = NEEDS_MORE_INFO
    message = factory.Faker('sentence')
    data = factory.Dict({'submission': factory.SelfAttribute('..submission')}, dict_factory=DeterminationDataFactory)

    is_draft = True
