from wagtail.admin.panels import InlinePanel


class ReadOnlyInlinePanel(InlinePanel):
    """
    Behaves same as InlinePanel, but removes UI for adding new item and
    deleting an existing item in the formset.
    """

    class BoundPanel(InlinePanel.BoundPanel):
        template_name = "core/wagtail/panels/inline_panel_readonly.html"
