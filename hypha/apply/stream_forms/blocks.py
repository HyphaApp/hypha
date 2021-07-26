# Credit to https://github.com/BertrandBordage for initial implementation
import bleach
from anyascii import anyascii
from dateutil.parser import isoparse, parse
from django import forms
from django.conf import settings
from django.db.models import BLANK_CHOICE_DASH
from django.forms.widgets import ClearableFileInput
from django.utils.dateparse import parse_datetime
from django.utils.encoding import force_str
from django.utils.html import conditional_escape
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_bleach.templatetags.bleach_tags import bleach_value
from wagtail.core.blocks import (
    BooleanBlock,
    CharBlock,
    ChoiceBlock,
    DateBlock,
    DateTimeBlock,
    IntegerBlock,
    ListBlock,
    RichTextBlock,
    StaticBlock,
    StreamBlock,
    StructBlock,
    TextBlock,
    TimeBlock,
    URLBlock,
)

from .fields import MultiFileField, SingleFileField


class FormFieldBlock(StructBlock):
    field_label = CharBlock(label=_('Label'))
    help_text = TextBlock(required=False, label=_('Help text'))
    help_link = URLBlock(required=False, label=_('Help link'))

    field_class = forms.CharField
    widget = None
    canonical_name = ""

    class Meta:
        template = 'stream_forms/render_field.html'

    def get_slug(self, struct_value):
        return force_str(slugify(anyascii(struct_value['field_label'])))

    def get_field_class(self, struct_value):
        return self.field_class

    def get_widget(self, struct_value):
        return self.widget

    def get_field_kwargs(self, struct_value):
        kwargs = {
            'label': struct_value['field_label'],
            'help_text': conditional_escape(struct_value['help_text']),
            'required': struct_value.get('required', False)
        }
        if 'default_value' in struct_value:
            kwargs['initial'] = struct_value['default_value']
        form_widget = self.get_widget(struct_value)
        if form_widget is not None:
            kwargs['widget'] = form_widget
        return kwargs

    def get_field(self, struct_value):
        field_kwargs = self.get_field_kwargs(struct_value)
        return self.get_field_class(struct_value)(**field_kwargs)

    def decode(self, value):
        """Convert JSON representation into actual python objects"""
        return value

    def serialize(self, value, context):
        field_kwargs = self.get_field_kwargs(value)
        return {
            'question': field_kwargs['label'],
            'answer': context.get('data'),
            'type': self.name,
        }

    def serialize_no_response(self, value, context):
        return {
            'question': value['field_label'],
            'answer': 'No Response',
            'type': 'no_response',
        }

    def prepare_data(self, value, data, serialize=False):
        return bleach_value(str(data))

    def render(self, value, context):
        data = context.get('data')
        data = self.prepare_data(value, data, context.get('serialize', False))

        context.update(data=data or self.no_response())

        if context.get('serialize'):
            if not data:
                return self.serialize_no_response(value, context)
            return self.serialize(value, context)

        return super().render(value, context)

    def get_searchable_content(self, value, data):
        return str(data)

    def no_response(self):
        return "No response"


class OptionalFormFieldBlock(FormFieldBlock):
    required = BooleanBlock(label=_('Required'), required=False)


CHARFIELD_FORMATS = [
    ('email', _('Email')),
    ('url', _('URL')),
]


class CharFieldBlock(OptionalFormFieldBlock):
    format = ChoiceBlock(choices=CHARFIELD_FORMATS, required=False, label=_('Format'))
    default_value = CharBlock(required=False, label=_('Default value'))

    class Meta:
        label = _('Text field (single line)')
        template = 'stream_forms/render_unsafe_field.html'

    def get_field_class(self, struct_value):
        text_format = struct_value['format']
        if text_format == 'url':
            return forms.URLField
        if text_format == 'email':
            return forms.EmailField
        return super().get_field_class(struct_value)

    def get_searchable_content(self, value, data):
        # CharField acts as a fallback. Force data to string
        data = str(data)
        return bleach.clean(data or '', tags=[], strip=True)


class MultiInputCharFieldBlock(CharFieldBlock):
    number_of_inputs = IntegerBlock(default=2, label=_('Max number of inputs'))
    add_button_text = CharBlock(required=False, default=_('Add new item'))

    class Meta:
        label = _('Text field (single line) (multiple inputs)')


class TextFieldBlock(OptionalFormFieldBlock):
    default_value = TextBlock(required=False, label=_('Default value'))
    word_limit = IntegerBlock(default=1000, label=_('Word limit'))

    widget = forms.Textarea(attrs={'rows': 5})

    class Meta:
        label = _('Text field (multi line)')
        template = 'stream_forms/render_unsafe_field.html'

    def get_searchable_content(self, value, data):
        return bleach.clean(data or '', tags=[], strip=True)


class NumberFieldBlock(OptionalFormFieldBlock):
    default_value = CharBlock(required=False, label=_('Default value'))

    widget = forms.NumberInput

    class Meta:
        label = _('Number field')

    def get_searchable_content(self, value, data):
        return None


class CheckboxFieldBlock(OptionalFormFieldBlock):
    default_value = BooleanBlock(required=False)

    field_class = forms.BooleanField

    class Meta:
        label = _('Checkbox field')
        icon = 'tick-inverse'

    def get_searchable_content(self, value, data):
        return None

    def no_response(self):
        return False


class RadioButtonsFieldBlock(OptionalFormFieldBlock):
    choices = ListBlock(CharBlock(label=_('Choice')))

    field_class = forms.ChoiceField
    widget = forms.RadioSelect

    class Meta:
        label = _('Radio buttons')
        icon = 'radio-empty'

    def get_field_kwargs(self, struct_value):
        kwargs = super().get_field_kwargs(struct_value)
        kwargs['choices'] = [
            (choice, choice)
            for choice in struct_value['choices']
        ]
        return kwargs


class GroupToggleBlock(FormFieldBlock):
    required = BooleanBlock(label=_('Required'), default=True)
    choices = ListBlock(
        CharBlock(label=_('Choice')),
        help_text=(
            'Please create only two choices for toggle. '
            'First choice will revel the group and the second hide it. '
            'Additional choices will be ignored.'
        )
    )

    field_class = forms.ChoiceField
    widget = forms.RadioSelect

    class Meta:
        label = _('Group fields')
        icon = 'group'
        help_text = 'Remember to end group using Group fields end block.'

    def get_field_kwargs(self, struct_value):
        kwargs = super().get_field_kwargs(struct_value)
        field_choices = [
            (choice, choice)
            for choice in struct_value['choices']
        ]
        total_choices = len(field_choices)
        if total_choices > 2:
            # For toggle we need only two choices
            field_choices = field_choices[:2]
        elif total_choices < 2:
            field_choices = [
                ('yes', 'Yes'),
                ('no', 'No'),
            ]
        kwargs['choices'] = field_choices
        return kwargs


class GroupToggleEndBlock(StaticBlock):
    class Meta:
        label = 'Group fields end'
        icon = 'group'
        admin_text = 'End of Group fields Block'


class DropdownFieldBlock(RadioButtonsFieldBlock):
    widget = forms.Select

    class Meta:
        label = _('Dropdown field')
        icon = 'arrow-down-big'

    def get_field_kwargs(self, struct_value):
        kwargs = super().get_field_kwargs(struct_value)
        kwargs['choices'].insert(0, BLANK_CHOICE_DASH[0])
        return kwargs


class CheckboxesFieldBlock(OptionalFormFieldBlock):
    checkboxes = ListBlock(CharBlock(label=_('Checkbox')))

    field_class = forms.MultipleChoiceField
    widget = forms.CheckboxSelectMultiple

    class Meta:
        label = _('Multiple checkboxes field')
        icon = 'list-ul'
        template = 'stream_forms/render_list_field.html'

    def get_field_kwargs(self, struct_value):
        kwargs = super().get_field_kwargs(struct_value)
        kwargs['choices'] = [
            (choice, choice)
            for choice in struct_value['checkboxes']
        ]
        return kwargs

    def prepare_data(self, value, data, serialize=False):
        base_prepare = super().prepare_data
        return [base_prepare(value, item, serialize) for item in data]

    def get_searchable_content(self, value, data):
        return data


class DatePickerInput(forms.DateInput):
    def __init__(self, *args, **kwargs):
        attrs = kwargs.get('attrs')
        if attrs is None:
            attrs = {}
        attrs.update({
            'data-provide': 'datepicker',
            'data-date-format': 'yyyy-mm-dd',
        })
        kwargs['attrs'] = attrs
        super().__init__(*args, **kwargs)


class DateFieldBlock(OptionalFormFieldBlock):
    default_value = DateBlock(required=False)

    field_class = forms.DateField
    widget = DatePickerInput

    class Meta:
        label = _('Date field')
        icon = 'date'

    def get_searchable_content(self, value, data):
        return None

    def decode(self, value):
        if value:
            return parse(value).date()


class HTML5TimeInput(forms.TimeInput):
    input_type = 'time'


class TimeFieldBlock(OptionalFormFieldBlock):
    default_value = TimeBlock(required=False)

    field_class = forms.TimeField
    widget = HTML5TimeInput

    class Meta:
        label = _('Time field')
        icon = 'time'

    def get_searchable_content(self, value, data):
        return None

    def decode(self, value):
        if value:
            return parse(value).time()


class DateTimePickerInput(forms.SplitDateTimeWidget):
    def __init__(self, attrs=None, date_format=None, time_format=None):
        super().__init__(attrs=attrs,
                         date_format=date_format, time_format=time_format)
        self.widgets = (
            DatePickerInput(attrs=attrs, format=date_format),
            HTML5TimeInput(attrs=attrs, format=time_format),
        )

    def decompress(self, value):
        if isinstance(value, str):
            value = parse_datetime(value)
        return super().decompress(value)


class DateTimeFieldBlock(OptionalFormFieldBlock):
    default_value = DateTimeBlock(required=False)

    field_class = forms.SplitDateTimeField
    widget = DateTimePickerInput

    class Meta:
        label = _('Date+time field')
        icon = 'date'

    def get_searchable_content(self, value, data):
        return None

    def decode(self, value):
        if value:
            return isoparse(value)


class UploadableMediaBlock(OptionalFormFieldBlock):
    class Meta:
        template = 'stream_forms/render_file_field.html'

    def get_searchable_content(self, value, data):
        return None

    def prepare_data(self, value, data, serialize):
        if serialize:
            if data:
                return data.serialize()
            return None

        return data


class ImageFieldBlock(UploadableMediaBlock):
    field_class = forms.ImageField
    widget = ClearableFileInput

    class Meta:
        label = _('Image field')
        icon = 'image'


class FileFieldBlock(UploadableMediaBlock):
    """This doesn't know how to save the uploaded files

    You must implement this if you want to reuse it.
    """
    field_class = SingleFileField

    class Meta:
        label = _('File field')
        icon = 'download'

    def get_field_kwargs(self, struct_value):
        kwargs = super().get_field_kwargs(struct_value)
        kwargs['help_text'] = kwargs['help_text'] + f" Accepted file types are {settings.FILE_ACCEPT_ATTR_VALUE}"
        return kwargs


class MultiFileFieldBlock(UploadableMediaBlock):
    field_class = MultiFileField

    class Meta:
        label = _('Multiple File field')
        template = 'stream_forms/render_multi_file_field.html'

    def get_field_kwargs(self, struct_value):
        kwargs = super().get_field_kwargs(struct_value)
        kwargs['help_text'] = kwargs['help_text'] + f" Accepted file types are {settings.FILE_ACCEPT_ATTR_VALUE}"
        return kwargs

    def prepare_data(self, value, data, serialize):
        if serialize:
            return [file.serialize() for file in data]
        return data

    def no_response(self):
        return [super().no_response()]


class HeadingBlock(StructBlock):
    HEADER_SIZE = [
        ('h2', 'H2'),
        ('h3', 'H3'),
        ('h4', 'H4')
    ]

    heading_text = CharBlock(classname="title", required=True)
    size = ChoiceBlock(choices=HEADER_SIZE, default='h2')

    class Meta:
        icon = "title"
        template = "stream_forms/heading_field.html"


class FormFieldsBlock(StreamBlock):
    text_markup = RichTextBlock(group=_('Custom'), label=_('Section text'))
    header_markup = HeadingBlock(group=_('Custom'), label=_('Section header'))
    char = CharFieldBlock(group=_('Fields'))
    multi_inputs_char = MultiInputCharFieldBlock(group=_('Fields'))
    text = TextFieldBlock(group=_('Fields'))
    number = NumberFieldBlock(group=_('Fields'))
    checkbox = CheckboxFieldBlock(group=_('Fields'))
    radios = RadioButtonsFieldBlock(group=_('Fields'))
    dropdown = DropdownFieldBlock(group=_('Fields'))
    checkboxes = CheckboxesFieldBlock(group=_('Fields'))
    date = DateFieldBlock(group=_('Fields'))
    time = TimeFieldBlock(group=_('Fields'))
    datetime = DateTimeFieldBlock(group=_('Fields'))
    image = ImageFieldBlock(group=_('Fields'))
    file = FileFieldBlock(group=_('Fields'))
    multi_file = MultiFileFieldBlock(group=_('Fields'))
    group_toggle = GroupToggleBlock(group=_("Custom"))
    group_toggle_end = GroupToggleEndBlock(group=_("Custom"))

    class Meta:
        label = _('Form fields')
