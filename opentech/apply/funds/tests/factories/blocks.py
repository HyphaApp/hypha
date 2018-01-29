import wagtail_factories

from opentech.apply.funds.blocks import CustomFormFieldsBlock


class CustomFormBlockFactory(wagtail_factories.StructBlockFactory):
    class Meta:
        model = CustomFormFieldsBlock
