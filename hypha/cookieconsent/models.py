from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.fields import RichTextField


@register_setting
class CookieConsentSettings(BaseGenericSetting):
    class Meta:
        verbose_name = _("Cookie banner settings")

    cookieconsent_active = models.BooleanField(
        _("Activate cookie pop-up banner"),
        default=False,
    )

    cookieconsent_title = models.CharField(
        _("Cookie banner title"),
        max_length=255,
        default=_("Your cookie settings"),
    )

    cookieconsent_message = RichTextField(
        _("Cookie consent message"),
        default=_(
            '<p>This website deploys cookies for basic functionality and to keep it secure. These cookies are strictly necessary. Optional analysis cookies which provide us with statistical information about the use of the website may also be deployed, but only with your consent. Please review our <a href="/data-privacy-policy/">Privacy &amp; Data Policy</a> for more information.</p>'
        ),
    )

    cookieconsent_essential_about = RichTextField(
        _('Essential cookies information to be displayed under "Learn More"'),
        default=_(
            "<p>Strictly necessary for the operation of a website because they enable you to navigate around the site and use features.  These cookies cannot be switched off in our systems and do not store any personally identifiable information.</p>"
        ),
    )

    cookieconsent_analytics = models.BooleanField(
        _("Include consent option for analytics cookies"),
        default=False,
    )

    cookieconsent_analytics_about = RichTextField(
        _('Analytics cookies information to be displayed under "Learn More"'),
        default=_(
            "<p>With these cookies we count visits and traffic sources to help improve the performance of our services through metrics.  These cookies show us which pages on our services are the most and the least popular, and how users navigate our services.  The information collected is aggregated and contains no personally identifiable information.  If you block these cookies, then we will not know when you have used our services.</p>"
        ),
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("cookieconsent_active"),
                FieldPanel("cookieconsent_title"),
                FieldPanel("cookieconsent_message"),
                FieldPanel("cookieconsent_essential_about"),
                FieldPanel("cookieconsent_analytics"),
                FieldPanel("cookieconsent_analytics_about"),
            ],
            _("Cookie banner"),
        ),
    ]
