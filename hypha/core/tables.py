import django_tables2 as tables
from django.conf import settings
from django.utils.html import format_html


class RelativeTimeColumn(tables.DateTimeColumn):
    def __init__(self, date_format=None, prefix="", **kwargs):
        self.date_format = date_format or settings.SHORT_DATETIME_FORMAT
        self.prefix = prefix
        super().__init__(**kwargs)

    def render(self, value):
        if not value:
            return "—"

        return format_html(
            "<relative-time datetime='{}' prefix='{}'>{}</relative-time>",
            value.isoformat(),
            self.prefix,
            value.strftime(self.date_format),
        )
