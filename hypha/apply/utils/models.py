from django.db import models
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.contrib.settings.models import BaseSetting, register_setting


@register_setting
class PDFPageSettings(BaseSetting):
    A4 = 'A4'
    LEGAL = 'legal'
    LETTER = 'letter'
    PAGE_SIZES = [
        (A4, 'A4'),
        (LEGAL, 'Legal'),
        (LETTER, 'Letter'),
    ]

    class Meta:
        verbose_name = 'pdf settings'

    download_page_size = models.CharField(
        choices=PAGE_SIZES,
        default=LEGAL,
        max_length=6,
        help_text='Page size of downloadable Project and Submission PDFs'
    )

    panels = [
        FieldPanel('download_page_size'),
    ]
