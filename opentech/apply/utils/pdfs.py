import os
import io

from reportlab.lib import pagesizes
from reportlab.lib.colors import Color, white
from reportlab.lib.styles import ParagraphStyle as PS
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

from bs4 import BeautifulSoup, NavigableString

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

DARK_GREY = Color(0.0154, 0.0154, 0, 0.7451)

PAGE_WIDTH, PAGE_HEIGHT = pagesizes.legal

MARGIN_LEFT = inch
MARGIN_TOP = inch
MARGIN_BOTTOM = 0.5 * inch


def make_pdf(title, meta, content):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

    blocks = [Spacer(1, 1 * inch)]
    extra_content = draw_content(content)
    blocks = [*blocks, *extra_content]

    def title_page(canvas, doc):
        canvas.setTitle(title)
        canvas.saveState()
        draw_title_block(canvas, title, meta)
        canvas.restoreState()

    def later_page(canvas, doc):
        canvas.saveState()
        draw_header(canvas, title)
        canvas.restoreState()

    doc.build(blocks, onFirstPage=title_page, onLaterPages=later_page)

    buffer.seek(0)
    return buffer


def draw_header(canvas, title):
    title_size = 10

    canvas.setFillColor(DARK_GREY)
    canvas.rect(
        0,
        PAGE_HEIGHT - MARGIN_TOP,
        PAGE_WIDTH,
        MARGIN_TOP,
        stroke=False,
        fill=True,
    )

    canvas.setFont("MontserratBold", title_size)
    canvas.setFillColor(white)
    pos = (PAGE_HEIGHT - MARGIN_TOP) + 2 * title_size
    canvas.drawString(
        MARGIN_LEFT,
        pos,
        title,
    )


def draw_title_block(canvas, title, meta):
    title_size = 30
    meta_size = 10
    header_height = MARGIN_TOP + title_size + 6 * meta_size

    canvas.setFillColor(DARK_GREY)
    canvas.rect(
        0,
        PAGE_HEIGHT - header_height,
        PAGE_WIDTH,
        header_height,
        stroke=False,
        fill=True,
    )

    canvas.setFont("MontserratBold", title_size)
    canvas.setFillColor(white)
    pos = PAGE_HEIGHT - (MARGIN_TOP + title_size)
    canvas.drawString(
        MARGIN_LEFT,
        pos,
        title,
    )

    canvas.setFont("Montserrat", meta_size)
    canvas.setFillColor(white)
    meta_text = '  |  '.join(str(text) for text in meta)

    pos -= meta_size * 3
    canvas.drawString(
        MARGIN_LEFT,
        pos,
        meta_text,
    )

    return PAGE_HEIGHT - header_height


def handle_block(block):
    RICH_TEXT_TAGS = ('p', 'ul', 'ol' 'h3', 'h2', 'h4', 'h5')

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
            elif tag.name == 'li':
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


