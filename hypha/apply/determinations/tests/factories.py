import random

import factory

from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory
from hypha.apply.stream_forms.testing.factories import (
    CharFieldBlockFactory,
    FormFieldBlockFactory,
    StreamFieldUUIDFactory,
)
from hypha.apply.utils.testing.factories import RichTextFieldBlockFactory

from ..blocks import DeterminationBlock, DeterminationMessageBlock, SendNoticeBlock
from ..models import Determination, DeterminationForm
from ..options import ACCEPTED, NEEDS_MORE_INFO, REJECTED
from ..views import get_form_for_stage


class DeterminationDataFactory(factory.DictFactory):
    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        submission = kwargs.pop("submission")
        action = kwargs.pop("action")
        form = get_form_for_stage(submission)(
            user=submission.lead, action=action, submission=submission
        )
        form_fields = {}

        form_fields = {
            field_name: 0
            for field_name, field in form.fields.items()
            if field_name not in form._meta.fields
        }

        form_fields.update(**kwargs)
        return super()._build(model_class, *args, **form_fields)


class DeterminationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Determination

    class Params:
        accepted = factory.Trait(outcome=ACCEPTED)
        rejected = factory.Trait(outcome=REJECTED)
        submitted = factory.Trait(is_draft=False)

    submission = factory.SubFactory(ApplicationSubmissionFactory)
    author = factory.SelfAttribute("submission.lead")

    outcome = NEEDS_MORE_INFO
    message = factory.Faker("sentence")
    data = factory.Dict(
        {
            "submission": factory.SelfAttribute("..submission"),
            "action": factory.SelfAttribute("..outcome"),
        },
        dict_factory=DeterminationDataFactory,
    )

    is_draft = True


class DeterminationBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = DeterminationBlock

    @classmethod
    def make_answer(cls, params=None):
        return random.choices([ACCEPTED, NEEDS_MORE_INFO, REJECTED])


class DeterminationMessageBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = DeterminationMessageBlock


class SendNoticeBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = SendNoticeBlock


DeterminationFormFieldsFactory = StreamFieldUUIDFactory(
    {
        "char": factory.SubFactory(CharFieldBlockFactory),
        "text": factory.SubFactory(RichTextFieldBlockFactory),
        "send_notice": factory.SubFactory(SendNoticeBlockFactory),
        "determination": factory.SubFactory(DeterminationBlockFactory),
        "message": factory.SubFactory(DeterminationMessageBlockFactory),
    }
)


class DeterminationFormFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DeterminationForm

    name = factory.Faker("word")
    form_fields = DeterminationFormFieldsFactory
