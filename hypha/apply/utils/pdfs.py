from io import BytesIO

from django.core.files import File
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from pypdf import PdfReader, PdfWriter
from xhtml2pdf import pisa

from hypha.apply.utils.models import PDFPageSettings


def html_to_pdf(html_body: str) -> BytesIO:
    """Convert HTML to PDF.

    Args:
        html_body: The body of the html as string

    Returns:
        BytesIO: PDF file
    """
    packet = BytesIO()
    pisa.CreatePDF(html_body, dest=packet, raise_exception=True, encoding="utf-8")
    packet.seek(0)
    return packet


def render_as_pdf(
    template_name: str, filename: str, context: dict, request=None
) -> HttpResponse:
    """Convert HTML template to PDF file and return as a downloadable file.

    Args:
        template_name: Django template name to render
        filename: Name of the output PDF file
        context: Context dictionary for rendering template
        request: Request object, defaults to None

    Returns:
        HttpResponse: PDF file as downloadable response

    Example:
        response = render_as_pdf(
            template_name='my_template.html',
            filename='my_pdf.pdf',
            context={'title': 'My PDF'},
            request=request
        )
    """
    if "pagesize" not in context:
        pdf_page_settings = PDFPageSettings.load(request_or_site=request)
        context["pagesize"] = pdf_page_settings.download_page_size

    context.setdefault("export_date", timezone.now())
    context.setdefault("export_user", request.user if request else None)

    html = render_to_string(
        template_name=template_name, context=context, request=request
    )
    pdf = html_to_pdf(html)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename={filename}"
    response.write(pdf.read())
    return response


def merge_pdf(origin_pdf: BytesIO, input_pdf: BytesIO) -> File:
    """Given two PDFs, merge them together.

    Args:
        origin_pdf: a file-like object containing a PDF
        input_pdf: a file-like object containing a PDF

    Returns:
        Return a File object containing the merged PDF and with the same name as the
        original PDF.
    """
    merger = PdfWriter(clone_from=BytesIO(origin_pdf.read()))
    merger.append(PdfReader(input_pdf))

    output_pdf = BytesIO()
    merger.write(output_pdf)
    output_pdf.seek(0)
    return File(output_pdf, name=origin_pdf.name)
