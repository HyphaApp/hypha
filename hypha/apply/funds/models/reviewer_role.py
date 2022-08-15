from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.settings.models import BaseSetting, register_setting

from hypha.apply.utils.image import generate_image_url


class ReviewerRole(models.Model):
    name = models.CharField(max_length=128)
    icon = models.ForeignKey(
        'images.CustomImage',
        null=True,
        blank=True,
        related_name='+',
        on_delete=models.SET_NULL
    )
    order = models.IntegerField(
        help_text=_('The order this role should appear in the Update Reviewers form.'),
        null=True,
        blank=True,
    )

    panels = [
        FieldPanel('name'),
        FieldPanel('icon'),
        FieldPanel('order'),
    ]

    def icon_url(self, filter_spec):
        return generate_image_url(self.icon, filter_spec)

    def __str__(self):
        return self.name


@register_setting
class ReviewerSettings(BaseSetting):
    SUBMISSIONS = [
        ('all', 'All Submissions'),
        ('reviewed', 'Only reviewed Submissions'),
    ]

    STATES = [
        ('all', 'All States'),
        ('ext_state_or_higher', 'Only External review and higher'),
        ('ext_state_only', 'Only External review')
    ]

    OUTCOMES = [
        ('all', 'All Outcomes'),
        ('all_except_dismissed', 'All Outcomes Except Dismissed'),
        ('accepted', 'Only Accepted')
    ]

    class Meta:
        verbose_name = 'Reviewer Settings'

    submission = models.CharField(
        choices=SUBMISSIONS,
        default='all',
        max_length=10,
        help_text=_('Submissions for which reviewers should have access to')
    )
    state = models.CharField(
        choices=STATES,
        default='all',
        max_length=20,
        help_text=_('Submissions states for which reviewers should have access to')
    )
    outcome = models.CharField(
        choices=OUTCOMES,
        default='all',
        max_length=20,
        help_text=_('Submissions outcomes for which reviewers should have access to')
    )
    assigned = models.BooleanField(
        default=False,
        help_text=_('Submissions for which reviewer is assigned to')
    )
    use_settings = models.BooleanField(
        default=False,
        help_text=_('Use the above configured variables to filter out submissions')
    )

    panels = [
        FieldPanel('submission'),
        FieldPanel('state'),
        FieldPanel('outcome'),
        FieldPanel('assigned'),
        FieldPanel('use_settings'),
    ]
