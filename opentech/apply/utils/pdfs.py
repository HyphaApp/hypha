import os
import io

from reportlab.lib import pagesizes
from reportlab.lib.colors import Color, white
from reportlab.lib.styles import ParagraphStyle as PS
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from bs4 import BeautifulSoup

styles = {
    'Normal': PS(fontName='NotoSans', name='Normal'),
    'Heading3': PS(fontName='MontserratBold', fontSize=16, name='Heading3', spaceAfter=4, spaceBefore=20, leading=24),
    'Heading4': PS(fontName='MontserratBold', fontSize=14, name='Heading4', spaceAfter=4, spaceBefore=18, leading=21),
    'Heading5': PS(fontName='MontserratBold', fontSize=12, name='Heading5', spaceAfter=4, spaceBefore=16, leading=18),
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
    title_size = 20
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


def draw_content(content):
    RICH_TEXT_TAGS = ('p', 'li', 'h3', 'h4', 'h5')

    paragraphs = []

    for section in BeautifulSoup(content, "html5lib").find_all('section'):
        for tag in section.find_all(RICH_TEXT_TAGS):
            text = tag.get_text()
            extra = {}
            if text:
                if tag.name in {'p'}:
                    style = styles['Normal']
                elif tag.name == 'li':
                    style = styles['Normal']
                    extra['bulletText'] = '•'
                elif tag.name == 'h3':
                    style = styles['Heading3']
                elif tag.name == 'h4':
                    style = styles['Heading4']
                elif tag.name == 'h5':
                    style = styles['Heading5']

                paragraphs.append(Paragraph(text, style, **extra))

    return paragraphs


