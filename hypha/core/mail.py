import logging
import re
from contextlib import contextmanager

import markdown
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist, loader
from django.utils import translation

logger = logging.getLogger(__name__)


@contextmanager
def language(lang):
    old_language = translation.get_language()
    try:
        translation.activate(lang)
        yield
    finally:
        translation.activate(old_language)


class MarkdownMail(object):
    template_name = None

    def __init__(self, template_name: str):
        self._email = None
        self.markdown_parser = markdown.Markdown(
            extensions=['markdown.extensions.tables']
        )

        if template_name is not None:
            self.template_name = template_name

    def _render_template(self, context):
        try:
            markdown_content = loader.render_to_string(self.template_name, context)
            return self.markdown_parser.convert(markdown_content)
        except TemplateDoesNotExist as e:
            logger.warning("Template '{0}' does not exists.".format(e))

    def _render_as_text(self):
        body_txt = u'\n'.join(self.markdown_parser.lines)
        return re.sub(r'\n\s*\n', '\n\r', body_txt)

    def make_email_object(self, to, context, **kwargs):
        if not isinstance(to, (list, tuple)):
            to = [to]

        lang = context.get('lang', None) or settings.LANGUAGE_CODE

        with language(lang):
            body_html = self._render_template(context)
            body_txt = self._render_as_text()

        email = EmailMultiAlternatives(**kwargs)
        email.body = body_txt
        email.attach_alternative(body_html, 'text/html')

        email.to = to  # type: ignore

        return email

    def send(self, to, context, **kwargs):
        email = self.make_email_object(to, context, **kwargs)
        return email.send()
