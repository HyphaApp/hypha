from tinymce.widgets import TinyMCE

MCE_ATTRIBUTES = {
    'elementpath': False,
    'branding': False,
    'toolbar1': 'undo redo | styleselect | bold italic | bullist numlist | link',
    'style_formats': [
        {'title': 'Headers', 'items': [
            {'title': 'Header 1', 'format': 'h1'},
            {'title': 'Header 2', 'format': 'h2'},
            {'title': 'Header 3', 'format': 'h3'},
        ]},
        {'title': 'Inline', 'items': [
            {'title': 'Bold', 'icon': 'bold', 'format': 'bold'},
            {'title': 'Italic', 'icon': 'italic', 'format': 'italic'},
            {'title': 'Underline', 'icon': 'underline', 'format': 'underline'},
        ]},
    ],
}
MCE_ATTRIBUTES_SHORT = {**MCE_ATTRIBUTES, **{'height': 180}}

RICH_TEXT_WIDGET = TinyMCE(mce_attrs=MCE_ATTRIBUTES)
RICH_TEXT_WIDGET_SHORT = TinyMCE(mce_attrs=MCE_ATTRIBUTES_SHORT)
