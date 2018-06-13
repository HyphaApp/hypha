from tinymce.widgets import TinyMCE


RICH_TEXT_WIDGET = TinyMCE(mce_attrs={
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
    'height': 180,
})
