import factory

from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory

from ..models import Determination, ACCEPTED, NEEDS_MORE_INFO, REJECTED, INVITED
from ..views import get_form_for_stage


class DeterminationDataFactory(factory.DictFactory):
    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        submission = kwargs.pop('submission')
        form = get_form_for_stage(submission)(user=submission.lead, submission=submission)
        form_fields = {}

        form_fields = {
            field_name: 0
            for field_name, field in form.fields.items()
            if field_name not in form._meta.fields
        }

        form_fields.update(**kwargs)
        return super()._build(model_class, *args, **form_fields)


class DeterminationFactory(factory.DjangoModelFactory):
    class Meta:
        model = Determination

    class Params:
        accepted = factory.Trait(outcome=ACCEPTED)
        rejected = factory.Trait(outcome=REJECTED)
        invited = factory.Trait(outcome=INVITED)
        submitted = factory.Trait(is_draft=False)

    submission = factory.SubFactory(ApplicationSubmissionFactory)
    author = factory.SelfAttribute('submission.lead')

    outcome = NEEDS_MORE_INFO
    message = factory.Faker('sentence')
    data = factory.Dict({'submission': factory.SelfAttribute('..submission')}, dict_factory=DeterminationDataFactory)

    is_draft = True
