# Generated by Django 3.2.18 on 2023-04-18 06:44

from django.db import migrations
import hypha.apply.categories.blocks
import hypha.apply.stream_forms.blocks
import wagtail.blocks
import wagtail.blocks.static_block
import wagtail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('funds', '0109_rename_section_text_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicationform',
            name='form_fields',
            field=wagtail.fields.StreamField([('text_markup', wagtail.blocks.RichTextBlock(group='Custom', label='Paragraph')), ('header_markup', wagtail.blocks.StructBlock([('heading_text', wagtail.blocks.CharBlock(form_classname='title', required=True)), ('size', wagtail.blocks.ChoiceBlock(choices=[('h2', 'H2'), ('h3', 'H3'), ('h4', 'H4')]))], group='Custom', label='Section header')), ('char', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('format', wagtail.blocks.ChoiceBlock(choices=[('email', 'Email'), ('url', 'URL')], label='Format', required=False)), ('default_value', wagtail.blocks.CharBlock(label='Default value', required=False))], group='Fields')), ('multi_inputs_char', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('format', wagtail.blocks.ChoiceBlock(choices=[('email', 'Email'), ('url', 'URL')], label='Format', required=False)), ('default_value', wagtail.blocks.CharBlock(label='Default value', required=False)), ('number_of_inputs', wagtail.blocks.IntegerBlock(default=2, label='Max number of inputs')), ('add_button_text', wagtail.blocks.CharBlock(default='Add new item', required=False))], group='Fields')), ('text', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('default_value', wagtail.blocks.TextBlock(label='Default value', required=False)), ('word_limit', wagtail.blocks.IntegerBlock(default=1000, label='Word limit'))], group='Fields')), ('number', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('default_value', wagtail.blocks.CharBlock(label='Default value', required=False))], group='Fields')), ('checkbox', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('default_value', wagtail.blocks.BooleanBlock(required=False))], group='Fields')), ('radios', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('choices', wagtail.blocks.ListBlock(wagtail.blocks.CharBlock(label='Choice')))], group='Fields')), ('dropdown', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('choices', wagtail.blocks.ListBlock(wagtail.blocks.CharBlock(label='Choice')))], group='Fields')), ('checkboxes', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('checkboxes', wagtail.blocks.ListBlock(wagtail.blocks.CharBlock(label='Checkbox')))], group='Fields')), ('date', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('default_value', wagtail.blocks.DateBlock(required=False))], group='Fields')), ('time', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('default_value', wagtail.blocks.TimeBlock(required=False))], group='Fields')), ('datetime', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('default_value', wagtail.blocks.DateTimeBlock(required=False))], group='Fields')), ('image', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False))], group='Fields')), ('file', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False))], group='Fields')), ('multi_file', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False))], group='Fields')), ('group_toggle', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(default=True, label='Required', required=False)), ('choices', wagtail.blocks.ListBlock(wagtail.blocks.CharBlock(label='Choice'), help_text='Please create only two choices for toggle. First choice will revel the group and the second hide it. Additional choices will be ignored.'))], group='Custom')), ('group_toggle_end', hypha.apply.stream_forms.blocks.GroupToggleEndBlock(group='Custom')), ('rich_text', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('default_value', wagtail.blocks.TextBlock(label='Default value', required=False)), ('word_limit', wagtail.blocks.IntegerBlock(default=1000, label='Word limit'))], group='Fields')), ('markdown_text', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('default_value', wagtail.blocks.TextBlock(label='Default value', required=False)), ('word_limit', wagtail.blocks.IntegerBlock(default=1000, label='Word limit'))], group='Fields')), ('category', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(help_text='Leave blank to use the default Category label', label='Label', required=False)), ('help_text', wagtail.blocks.TextBlock(help_text='Leave blank to use the default Category help text', label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('category', wagtail.blocks.ChoiceBlock(choices=hypha.apply.categories.blocks.get_categories_as_choices)), ('multi', wagtail.blocks.BooleanBlock(label='Multi select', required=False))], group='Custom')), ('title', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(default='What is the title of your application?', label='Label')), ('help_text', wagtail.blocks.TextBlock(default='This project name can be changed if a full proposal is requested.', label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('info', wagtail.blocks.static_block.StaticBlock())], group=' Required')), ('email', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(default='What email address should we use to contact you?', label='Label')), ('help_text', wagtail.blocks.TextBlock(default='We will use this email address to communicate with you about your proposal.', label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('info', wagtail.blocks.static_block.StaticBlock())], group=' Required')), ('full_name', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(default='What is your name?', label='Label')), ('help_text', wagtail.blocks.TextBlock(default='We will use this name when we communicate with you about your proposal.', label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('info', wagtail.blocks.static_block.StaticBlock())], group=' Required')), ('value', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('info', wagtail.blocks.static_block.StaticBlock())], group='Custom')), ('address', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('info', wagtail.blocks.static_block.StaticBlock())], group='Custom')), ('duration', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('duration_type', wagtail.blocks.ChoiceBlock(choices=[('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months')], help_text='Duration type is used to display duration choices in Days, Weeks or Months in application forms. Be careful, changing the duration type in the active round can result in data inconsistency.')), ('info', wagtail.blocks.static_block.StaticBlock())], group='Custom'))], use_json_field=True),
        ),
        migrations.AlterField(
            model_name='applicationsubmission',
            name='form_fields',
            field=wagtail.fields.StreamField([('text_markup', wagtail.blocks.RichTextBlock(group='Custom', label='Paragraph')), ('header_markup', wagtail.blocks.StructBlock([('heading_text', wagtail.blocks.CharBlock(form_classname='title', required=True)), ('size', wagtail.blocks.ChoiceBlock(choices=[('h2', 'H2'), ('h3', 'H3'), ('h4', 'H4')]))], group='Custom', label='Section header')), ('char', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('format', wagtail.blocks.ChoiceBlock(choices=[('email', 'Email'), ('url', 'URL')], label='Format', required=False)), ('default_value', wagtail.blocks.CharBlock(label='Default value', required=False))], group='Fields')), ('multi_inputs_char', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('format', wagtail.blocks.ChoiceBlock(choices=[('email', 'Email'), ('url', 'URL')], label='Format', required=False)), ('default_value', wagtail.blocks.CharBlock(label='Default value', required=False)), ('number_of_inputs', wagtail.blocks.IntegerBlock(default=2, label='Max number of inputs')), ('add_button_text', wagtail.blocks.CharBlock(default='Add new item', required=False))], group='Fields')), ('text', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('default_value', wagtail.blocks.TextBlock(label='Default value', required=False)), ('word_limit', wagtail.blocks.IntegerBlock(default=1000, label='Word limit'))], group='Fields')), ('number', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('default_value', wagtail.blocks.CharBlock(label='Default value', required=False))], group='Fields')), ('checkbox', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('default_value', wagtail.blocks.BooleanBlock(required=False))], group='Fields')), ('radios', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('choices', wagtail.blocks.ListBlock(wagtail.blocks.CharBlock(label='Choice')))], group='Fields')), ('dropdown', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('choices', wagtail.blocks.ListBlock(wagtail.blocks.CharBlock(label='Choice')))], group='Fields')), ('checkboxes', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('checkboxes', wagtail.blocks.ListBlock(wagtail.blocks.CharBlock(label='Checkbox')))], group='Fields')), ('date', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('default_value', wagtail.blocks.DateBlock(required=False))], group='Fields')), ('time', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('default_value', wagtail.blocks.TimeBlock(required=False))], group='Fields')), ('datetime', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('default_value', wagtail.blocks.DateTimeBlock(required=False))], group='Fields')), ('image', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False))], group='Fields')), ('file', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False))], group='Fields')), ('multi_file', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False))], group='Fields')), ('group_toggle', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(default=True, label='Required', required=False)), ('choices', wagtail.blocks.ListBlock(wagtail.blocks.CharBlock(label='Choice'), help_text='Please create only two choices for toggle. First choice will revel the group and the second hide it. Additional choices will be ignored.'))], group='Custom')), ('group_toggle_end', hypha.apply.stream_forms.blocks.GroupToggleEndBlock(group='Custom')), ('rich_text', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('default_value', wagtail.blocks.TextBlock(label='Default value', required=False)), ('word_limit', wagtail.blocks.IntegerBlock(default=1000, label='Word limit'))], group='Fields')), ('markdown_text', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('default_value', wagtail.blocks.TextBlock(label='Default value', required=False)), ('word_limit', wagtail.blocks.IntegerBlock(default=1000, label='Word limit'))], group='Fields')), ('category', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(help_text='Leave blank to use the default Category label', label='Label', required=False)), ('help_text', wagtail.blocks.TextBlock(help_text='Leave blank to use the default Category help text', label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('category', wagtail.blocks.ChoiceBlock(choices=hypha.apply.categories.blocks.get_categories_as_choices)), ('multi', wagtail.blocks.BooleanBlock(label='Multi select', required=False))], group='Custom')), ('title', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(default='What is the title of your application?', label='Label')), ('help_text', wagtail.blocks.TextBlock(default='This project name can be changed if a full proposal is requested.', label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('info', wagtail.blocks.static_block.StaticBlock())], group=' Required')), ('email', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(default='What email address should we use to contact you?', label='Label')), ('help_text', wagtail.blocks.TextBlock(default='We will use this email address to communicate with you about your proposal.', label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('info', wagtail.blocks.static_block.StaticBlock())], group=' Required')), ('full_name', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(default='What is your name?', label='Label')), ('help_text', wagtail.blocks.TextBlock(default='We will use this name when we communicate with you about your proposal.', label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('info', wagtail.blocks.static_block.StaticBlock())], group=' Required')), ('value', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('info', wagtail.blocks.static_block.StaticBlock())], group='Custom')), ('address', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('info', wagtail.blocks.static_block.StaticBlock())], group='Custom')), ('duration', wagtail.blocks.StructBlock([('field_label', wagtail.blocks.CharBlock(label='Label')), ('help_text', wagtail.blocks.TextBlock(label='Help text', required=False)), ('help_link', wagtail.blocks.URLBlock(label='Help link', required=False)), ('required', wagtail.blocks.BooleanBlock(label='Required', required=False)), ('duration_type', wagtail.blocks.ChoiceBlock(choices=[('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months')], help_text='Duration type is used to display duration choices in Days, Weeks or Months in application forms. Be careful, changing the duration type in the active round can result in data inconsistency.')), ('info', wagtail.blocks.static_block.StaticBlock())], group='Custom'))], use_json_field=True),
        ),
    ]
