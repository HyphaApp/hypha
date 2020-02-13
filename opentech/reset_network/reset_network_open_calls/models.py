from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models
from django.http import HttpResponseRedirect
from django.shortcuts import render
from opentech.apply.activity.tasks import send_mail
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel, PageChooserPanel
from wagtail.core.models import Page
from django.contrib import messages


class ResetNetworkOpenCallsPage(Page):
    class Meta:
        verbose_name = "Reset Network Open Calls Page"

    parent_page_types = ['reset_network_home.ResetNetworkHomePage']
    subpage_types = ['reset_network_open_calls.ResetNetworkOpenCallPage']

    content_heading = models.CharField(verbose_name='Heading', max_length=255, blank=False)
    content_text = models.TextField(verbose_name='Text', blank=True)

    no_open_calls_heading = models.CharField(verbose_name='Heading', max_length=255, blank=False)
    no_open_calls_text = models.TextField(verbose_name='Text', blank=True)
    no_open_calls_success = models.TextField(verbose_name='Success Message', blank=False)

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('content_heading'),
            FieldPanel('content_text'),
        ], heading='Content'),
        MultiFieldPanel([
            FieldPanel('no_open_calls_heading'),
            FieldPanel('no_open_calls_text'),
            FieldPanel('no_open_calls_success'),
        ], heading='Content - No Open Calls'),
    ]

    def get_context(self, request, *args, **kwargs):

        open_calls = ResetNetworkOpenCallPage.objects.live().public()

        paginator = Paginator(open_calls, 8)
        page = request.GET.get("page")

        try:
            open_calls = paginator.page(page)
        except PageNotAnInteger:
            open_calls = paginator.page(1)
        except EmptyPage:
            open_calls = paginator.page(paginator.num_pages)

        context = super().get_context(request, *args, **kwargs)
        context['open_calls'] = open_calls
        return context

    def serve(self, request):

        from opentech.reset_network.reset_network_open_calls.forms import ResetNetworkOpenCallsForm

        context = self.get_context(request)

        if request.method == 'POST':
            form = ResetNetworkOpenCallsForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data.copy()
                name = data.get('name', 'unknown')
                email = data.get('email', settings.ORG_EMAIL)

                subject = f"{settings.ORG_LONG_NAME}: open call opportunities subscription"
                message = f"Name: {name}\nEmail: {email}"

                send_mail(
                    subject,
                    message,
                    email,
                    [settings.ORG_EMAIL],
                    logs=[]  # cant omit as the code falls over
                )
                messages.success(request, self.no_open_calls_success)
                return HttpResponseRedirect('#success')
            else:
                # should not get here
                messages.error(request, 'Invalid')
        else:
            form = ResetNetworkOpenCallsForm()

        context['form'] = form
        return render(
            request,
            self.get_template(request),
            context
        )


class ResetNetworkOpenCallPage(Page):
    class Meta:
        verbose_name = "Reset Network Open Call Page"

    parent_page_types = ['reset_network_open_calls.ResetNetworkOpenCallsPage']
    subpage_types = []

    content_heading = models.CharField(verbose_name='Heading', max_length=255, blank=False)
    content_text = RichTextField(verbose_name='Text', blank=False)

    fund = models.ForeignKey(
        'wagtailcore.Page',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    card_heading = models.CharField(max_length=100, blank=False)
    card_text = models.TextField(blank=True)

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('content_heading'),
            FieldPanel('content_text'),
        ], 'Content'),
        MultiFieldPanel([
            PageChooserPanel('fund', 'funds.FundType'),
        ], 'Fund Details'),
        MultiFieldPanel([
            FieldPanel('card_heading'),
            FieldPanel('card_text'),
        ], heading='Card Details'),
    ]

    @property
    def is_open(self):
        return self.fund and bool(self.fund.specific.open_round)

    @property
    def deadline(self):
        return self.fund and self.fund.specific.next_deadline()
