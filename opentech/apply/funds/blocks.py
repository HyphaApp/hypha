from django.utils.translation import ugettext_lazy as _

from opentech.apply.stream_forms.blocks import FormFieldsBlock

from opentech.apply.categories.blocks import CategoryQuestionBlock


class CustomFormFieldsBlock(FormFieldsBlock):
    category = CategoryQuestionBlock(group=_('Custom'))
