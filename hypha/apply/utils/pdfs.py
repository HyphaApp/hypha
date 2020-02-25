import io
import os

from bs4 import BeautifulSoup, NavigableString
from reportlab.lib import pagesizes
from reportlab.lib.colors import Color, white
from reportlab.lib.styles import ParagraphStyle as PS
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

styles = {
    'Question': PS(fontName='MontserratBold', fontSize=14, name='Question', spaceAfter=0, spaceBefore=18, leading=21),
    'Normal': PS(fontName='NotoSans', name='Normal'),
    'Heading1': PS(fontName='NotoSansBold', fontSize=12, name='Heading1', spaceAfter=4, spaceBefore=12, leading=18),
    'Heading2': PS(fontName='NotoSansBold', fontSize=10, name='Heading2', spaceAfter=4, spaceBefore=10, leading=15),
    'Heading3': PS(fontName='NotoSansBold', fontSize=10, name='Heading3', spaceAfter=4, spaceBefore=10, leading=15),
    'Heading4': PS(fontName='NotoSansBold', fontSize=10, name='Heading4', spaceAfter=4, spaceBefore=10, leading=15),
    'Heading5': PS(fontName='NotoSansBold', fontSize=10, name='Heading5', spaceAfter=4, spaceBefore=10, leading=15),
}

font_location = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media', 'fonts')


def font(font_name):
    return os.path.join(font_location, font_name)


PREPARED_FONTS = False


def prepare_fonts():
    global PREPARED_FONTS
    if PREPARED_FONTS:
        return
    pdfmetrics.registerFont(TTFont('Montserrat', font('Montserrat-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('MontserratBold', font('Montserrat-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('MontserratItalic', font('Montserrat-Italic.ttf')))
    pdfmetrics.registerFont(TTFont('MontserratBoldItalic', font('Montserrat-BoldItalic.ttf')))
    pdfmetrics.registerFontFamily(
        'Montserrat',
        normal='Montserrat',
        bold='MontserratBold',
        italic='MontserratItalic',
        boldItalic='MontserratBoldItalic'
    )

    pdfmetrics.registerFont(TTFont('NotoSans', font('NotoSans-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('NotoSansBold', font('NotoSans-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('NotoSansItalic', font('NotoSans-Italic.ttf')))
    pdfmetrics.registerFont(TTFont('NotoSansBoldItalic', font('NotoSans-BoldItalic.ttf')))
    pdfmetrics.registerFontFamily(
        'NotoSans',
        normal='NotoSans',
        bold='NotoSansBold',
        italic='NotoSansItalic',
        boldItalic='NotoSansBoldItalic'
    )
    PREPARED_FONTS = True


DARK_GREY = Color(0.0154, 0.0154, 0, 0.7451)

PAGE_WIDTH, PAGE_HEIGHT = pagesizes.legal

# default value from https://github.com/MrBitBucket/reportlab-mirror/blob/58fb7bd37ee956cea45477c8b5aef723f1cb82e5/src/reportlab/platypus/frames.py#L70
FRAME_PADDING = 6


def make_pdf(title, meta, content):
    prepare_fonts()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
        title=title,
    )

    blocks = []
    extra_content = draw_content(content)
    blocks = [*blocks, *extra_content]

    def title_page(canvas, doc):
        canvas.saveState()
        title_spacer = draw_title_block(canvas, doc, title, meta)
        canvas.restoreState()
        blocks.insert(0, title_spacer)

    def later_page(canvas, doc):
        canvas.saveState()
        draw_header(canvas, doc, title)
        canvas.restoreState()

    doc.build(blocks, onFirstPage=title_page, onLaterPages=later_page)

    buffer.seek(0)
    return buffer


def split_text(canvas, text, width):
    return simpleSplit(text, canvas._fontname, canvas._fontsize, width)


def draw_header(canvas, doc, title):
    title_size = 10

    canvas.setFillColor(DARK_GREY)
    canvas.rect(
        0,
        PAGE_HEIGHT - doc.topMargin,
        PAGE_WIDTH,
        doc.topMargin,
        stroke=False,
        fill=True,
    )
    # Set canvas font to correctly calculate the splitting

    canvas.setFont("MontserratBold", title_size)
    canvas.setFillColor(white)

    text_width = PAGE_WIDTH - doc.leftMargin - doc.rightMargin - 2 * FRAME_PADDING
    split_title = split_text(canvas, title, text_width)

    pos = (
        (PAGE_HEIGHT - doc.topMargin) +  # bottom of top margin
        1.5 * len(split_title) * title_size +  # text
        title_size / 2  # bottom padding
    )

    for line in split_title:
        pos -= title_size
        canvas.drawString(
            doc.leftMargin + FRAME_PADDING,
            pos,
            line,
        )
        pos -= title_size / 2


def draw_title_block(canvas, doc, title, meta):
    title_size = 30
    meta_size = 10

    text_width = PAGE_WIDTH - doc.leftMargin - doc.rightMargin - 2 * FRAME_PADDING

    # Set canvas font to correctly calculate the splitting
    canvas.setFont("MontserratBold", title_size)
    canvas.setFillColor(white)
    split_title = split_text(canvas, title, text_width)

    total_height = (
        doc.topMargin +
        len(split_title) * (title_size + title_size / 2) +  # title + spacing
        meta_size * 4  # 1 for text 3 for spacing
    )

    canvas.setFillColor(DARK_GREY)
    canvas.rect(
        0,
        PAGE_HEIGHT - total_height,
        PAGE_WIDTH,
        total_height,
        stroke=False,
        fill=True,
    )

    canvas.setFont("MontserratBold", title_size)
    canvas.setFillColor(white)
    pos = PAGE_HEIGHT - doc.topMargin

    for line in split_title:
        pos -= title_size
        canvas.drawString(
            doc.leftMargin + FRAME_PADDING,
            pos,
            line,
        )
        pos -= title_size / 2

    canvas.setFont("MontserratBold", meta_size)
    canvas.setFillColor(white)
    meta_text = '  |  '.join(str(text) for text in meta)

    pos -= meta_size * 2
    canvas.drawString(
        doc.leftMargin + FRAME_PADDING,
        pos,
        meta_text,
    )

    return Spacer(1, total_height - doc.topMargin)


def handle_block(block):
    paragraphs = []

    for tag in block:
        if isinstance(tag, NavigableString):
            text = tag.strip()
            if text:
                paragraphs.append(Paragraph(text, styles['Normal']))
        elif tag.name in {'ul', 'ol'}:
            style = styles['Normal']
            if tag.name == 'ul':
                bullet = 'bullet'
            elif tag.name == 'ol':
                bullet = '1'

            paragraphs.append(
                ListFlowable(
                    [
                        ListItem(Paragraph(bullet_item.get_text(), style))
                        for bullet_item in tag.find_all('li')
                    ],
                    bulletType=bullet,
                )
            )
        elif tag.name in {'table'}:
            paragraphs.append(
                Table(
                    [
                        [
                            Paragraph(cell.get_text(), styles['Normal'])
                            for cell in row.find_all({'td', 'th'})
                        ]
                        for row in tag.find_all('tr')
                    ],
                    colWidths='*',
                    style=TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LINEABOVE', (0, 0), (-1, -1), 1, DARK_GREY),
                    ]),
                )
            )
        else:
            if tag.name in {'p'}:
                style = styles['Normal']
            elif tag.name == 'h2':
                style = styles['Heading2']
            elif tag.name == 'h3':
                style = styles['Heading3']
            elif tag.name == 'h4':
                style = styles['Heading4']
            elif tag.name == 'h5':
                style = styles['Heading5']

            text = tag.get_text()
            if text:
                paragraphs.append(Paragraph(text, style))
    return paragraphs


def draw_content(content):
    paragraphs = []

    for section in BeautifulSoup(content, "html5lib").find_all('section'):
        question_text = section.select_one('.question').get_text()
        question = Paragraph(question_text, styles['Question'])

        # Keep the question and the first block of the answer together
        # this keeps 1 line answers tidy and ensures that bigger responses break
        # sooner instead of waiting to fill an entire page. There may still be issues
        first_answer, *rest = handle_block(section.select_one('.answer'))
        paragraphs.extend([
            KeepTogether([
                question,
                first_answer,
            ]),
            *rest
        ])
    return paragraphs
