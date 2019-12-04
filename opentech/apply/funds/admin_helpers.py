from urllib.parse import urlencode

from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _

from wagtail.contrib.modeladmin.forms import ParentChooserForm
from wagtail.contrib.modeladmin.helpers import PageAdminURLHelper, PageButtonHelper, ButtonHelper
from wagtail.contrib.modeladmin.views import ChooseParentView
from wagtail.core.models import Page


class VerboseLabelModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(str, obj):
        return '[{}] {}'.format(obj._meta.verbose_name, obj.title)


class FundChooserForm(ParentChooserForm):
    """Changes the default chooser to be fund orientated """
    parent_page = VerboseLabelModelChoiceField(
        label=_('Fund or RFP'),
        required=True,
        empty_label=None,
        queryset=Page.objects.none(),
        widget=forms.RadioSelect(),
    )


class RoundFundChooserView(ChooseParentView):
    def get_form(self, request):
        parents = self.permission_helper.get_valid_parent_pages(request.user).specific()
        return FundChooserForm(parents, request.POST or None)


class ButtonsWithPreview(PageButtonHelper):
    def preview_button(self, obj, classnames_add, classnames_exclude):
        classnames = self.copy_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': reverse('wagtailadmin_pages:view_draft', args=(obj.id,)),
            'label': 'Preview',
            'classname': cn,
            'title': 'Preview this %s' % self.verbose_name,
        }

    def get_buttons_for_obj(self, obj, exclude=list(), classnames_add=list(),
                            classnames_exclude=list()):
        btns = super().get_buttons_for_obj(obj, exclude, classnames_add, classnames_exclude)

        # Put preview before delete
        btns.insert(-1, self.preview_button(obj, classnames_add, classnames_exclude))

        return btns


class FormsFundRoundListFilter(admin.SimpleListFilter):
    title = 'usage'
    parameter_name = 'form-usage'

    def lookups(self, request, model_admin):
        return (
            ('applicationbase', _('Funds & RFP')),
            ('roundbase', _('Rounds and Sealed Rounds')),
            ('labbase', _('Labs')),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            query = {f'{value}form__isnull': False}
            return queryset.filter(**query).distinct()
        return queryset


class RoundStateListFilter(admin.SimpleListFilter):
    title = 'state'
    parameter_name = 'form-state'

    def lookups(self, request, model_admin):
        return (
            ('open', _('Open')),
            ('closed', _('Closed')),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'open':
            return queryset.open()
        elif value == 'closed':
            return queryset.closed()
        return queryset


class ApplicationFormButtonHelper(ButtonHelper):
    def prepare_classnames(self, start=None, add=None, exclude=None):
        """Parse classname sets into final css classess list."""
        classnames = start or []
        classnames.extend(add or [])
        return self.finalise_classname(classnames, exclude or [])

    def copy_form_button(self, pk, form_name, **kwargs):
        classnames = self.prepare_classnames(
            start=self.edit_button_classnames,
            add=kwargs.get('classnames_add'),
            exclude=kwargs.get('classnames_exclude')
        )
        return {
            'classname': classnames,
            'label': f'Copy',
            'title': f'Copy {form_name}',
            'url': self.url_helper.get_action_url('copy_form', admin.utils.quote(pk)),
        }

    def get_buttons_for_obj(self, obj, exclude=None, *args, **kwargs):
        """Override the getting of buttons, appending copy form button."""
        buttons = super().get_buttons_for_obj(obj, *args, **kwargs)

        copy_form_button = self.copy_form_button(
            pk=getattr(obj, self.opts.pk.attname),
            form_name=getattr(obj, 'name'),
            **kwargs
        )
        buttons.append(copy_form_button)

        return buttons


class RoundAdminURLHelper(PageAdminURLHelper):
    @cached_property
    def index_url(self):
        # By default set open filter and sort on end date
        # for Round listing page's index URL
        params = {'form-state': 'open', 'o': '-3'}
        return f"{self.get_action_url('index')}?{urlencode(params)}"
