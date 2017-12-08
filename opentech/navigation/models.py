from django.db import models

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel, InlinePanel,
    PageChooserPanel
)
from wagtail.wagtailcore.models import Orderable
from wagtail.wagtailsnippets.models import register_snippet

from opentech.esi import purge_esi


class AbstractBaseNavigationSnippet(ClusterableModel):
    """
    Classes inheriting from this _must_ define a `role` attribute to populate
    the help_text sensibly.
    """
    def __init__(self, *args, **kwargs):
        super(AbstractBaseNavigationSnippet, self).__init__(*args, **kwargs)
        [f for f in self._meta.fields if f.name == "menu_item"][0].help_text = "Pick a page you wish to include in the %(role)s navigation" % {'role': self.role}

    menu_item = models.ForeignKey(
        'wagtailcore.Page',
        on_delete=models.CASCADE,
        related_name='+'
    )
    menu_label = models.CharField(max_length=255, blank=True, help_text="If you wish to use a label different from the page title please enter it here.")
    order = models.IntegerField(help_text="Menu entries are displayed in ascending order.", default="100")
    role = ""

    class Meta:
        abstract = True
        ordering = ['order']

    def __str__(self):
        return self.menu_label or self.menu_item.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        purge_esi()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        purge_esi()

    panels = [
        PageChooserPanel('menu_item'),
        FieldPanel('menu_label', classname="full"),
        FieldPanel('order', classname="full"),
    ]


class PrimaryNavigationSubmenuSnippet(AbstractBaseNavigationSnippet, Orderable):
    parent = ParentalKey('PrimaryNavigationSnippet', related_name='submenus')
    role = "Primary Submenu"

    class Meta:
        ordering = ['sort_order']

    panels = [
        PageChooserPanel('menu_item'),
        FieldPanel('menu_label', classname="full"),
    ]


class PrimaryNavigationSnippet(AbstractBaseNavigationSnippet):
    role = "Primary"

    panels = AbstractBaseNavigationSnippet.panels + [
        InlinePanel('submenus', label="Submenus"),
    ]


register_snippet(PrimaryNavigationSnippet)


class SecondaryNavigationSnippet(AbstractBaseNavigationSnippet):
    role = "Secondary"


register_snippet(SecondaryNavigationSnippet)


class FooterNavigationSnippet(AbstractBaseNavigationSnippet):
    role = "Footer"


register_snippet(FooterNavigationSnippet)
