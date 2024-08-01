from tinymce.widgets import TinyMCE

MCE_ATTRIBUTES = {
    "elementpath": False,
    "branding": False,
    "contextmenu": False,
    "entity_encoding": "raw",
    "plugins": "link table lists wordcount",
    "toolbar": "undo redo | blocks | bold italic | bullist numlist | table | link",
    "relative_urls": False,
    "browser_spellcheck": True,
    "default_link_target": "_blank",
    "invalid_elements": "iframe,object,embed",
}
MCE_ATTRIBUTES_SHORT = {**MCE_ATTRIBUTES, **{"height": 180}}

RICH_TEXT_WIDGET = TinyMCE(mce_attrs=MCE_ATTRIBUTES)
RICH_TEXT_WIDGET_SHORT = TinyMCE(mce_attrs=MCE_ATTRIBUTES_SHORT)
