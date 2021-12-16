import logging
import uuid
from urllib.parse import urlparse

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import RedirectView
from django.views.generic.edit import FormMixin
from mailchimp3 import MailChimp

from .forms import NewsletterForm

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class MailchimpSubscribeView(FormMixin, RedirectView):
    form_class = NewsletterForm

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        self.error(form)
        return HttpResponseRedirect(self.get_success_url())

    def form_valid(self, form):
        mailchimp_enabled = settings.MAILCHIMP_API_KEY and settings.MAILCHIMP_LIST_ID

        dummy_key = 'a' * 32

        client = MailChimp(mc_api=settings.MAILCHIMP_API_KEY or dummy_key, timeout=5.0, enabled=mailchimp_enabled)

        data = form.cleaned_data.copy()
        email = data.pop('email')
        data = {
            k.upper(): v
            for k, v in data.items()
        }
        try:
            client.lists.members.create(settings.MAILCHIMP_LIST_ID, {
                'email_address': email,
                'status': 'pending',
                'merge_fields': data,
            })
        except Exception as e:
            self.warning(e)
        else:
            if mailchimp_enabled:
                self.success()
            else:
                self.warning(Exception(
                    'Incorrect Mailchimp configuration: API_KEY: {}, LIST_ID: {}'.format(
                        str(settings.MAILCHIMP_API_KEY),
                        str(settings.MAILCHIMP_LIST_ID),
                    )
                ))

        return super().form_valid(form)

    def error(self, form):
        messages.error(self.request, _('Sorry, there were errors with your form.') + str(form.errors))

    def warning(self, e):
        messages.warning(self.request, _('Sorry, there has been an problem. Please try again later.'))
        # If there is a problem with subscribing uncomment this to get notifications.
        # When things work warnings is only about spam scipts.
        # logger.error(e.args[0])

    def success(self):
        messages.success(self.request, _('Thank you for subscribing'))

    def get_success_url(self):
        # Go back to where you came from, default to front page.
        origin = '/'
        if urlparse(self.request.META.get('HTTP_ORIGIN')).hostname in settings.ALLOWED_HOSTS:
            origin = self.request.META.get('HTTP_ORIGIN')
        elif urlparse(self.request.META.get('HTTP_REFERER')).hostname in settings.ALLOWED_HOSTS:
            origin = self.request.META.get('HTTP_REFERER')

        # Add cache busting query string.
        return origin + '?newsletter-' + uuid.uuid4().hex

    def get_redirect_url(self):
        # We don't know where you came from, go home
        return '/'
