import logging
import re
from contextlib import contextmanager
from typing import Dict, List

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist, loader
from django.utils import translation

from hypha.core.utils import markdown_to_html

logger = logging.getLogger(__name__)


def cleanup_markdown(text):
    """Removes extra blank lines and spaces from markdown generated
    using Django templates. Do this for readably of markdown itself.
    """
    return re.sub(r'\n\s*\n', '\n\r', text)


@contextmanager
def language(lang):
    old_language = translation.get_language()
    try:
        translation.activate(lang)
        yield
    finally:
        translation.activate(old_language)


class MarkdownMail(object):
    """Render and send an html + plain-text email using a markdown template.

    Usages:
    >>> email = MarkdownMail("messages/email/send_reset_email.md")
    >>> email.send(to='xyz@email.com', from=settings.DEFAULT_FROM_EMAIL, context={'key': 'value'})

    Translates the email based on Django settings or 'lang' parameter
    available in the context.

    Adds `Auto-Submitted` header.
    """

    template_name = ''

    def __init__(self, template_name: str):
        self._email = None

        if template_name is not None:
            self.template_name = template_name

    def _render_template(self, context: Dict) -> str:
        try:
            return loader.render_to_string(self.template_name, context)
        except TemplateDoesNotExist as e:
            logger.warning("Template '{0}' does not exists.".format(e))

    def make_email_object(self, to: str | List[str], context, **kwargs):
        if not isinstance(to, (list, tuple)):
            to = [to]

        lang = context.get('lang', None) or settings.LANGUAGE_CODE

        with language(lang):
            rendered_template = self._render_template(context)
            body_txt = cleanup_markdown(rendered_template)
            body_html = markdown_to_html(rendered_template)

        email = EmailMultiAlternatives(**kwargs)
        email.body = body_txt
        email.attach_alternative(body_html, 'text/html')

        email.to = to

        return email

    def send(self, to: str | List[str], context, **kwargs):
        kwargs.setdefault('headers', {})
        kwargs['headers'].update({'Auto-Submitted': 'auto-generated'})

        email = self.make_email_object(to, context, **kwargs)
        return email.send()
