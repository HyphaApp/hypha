from wagtail.admin.forms import WagtailAdminModelForm

from hypha.apply.users.groups import GROUPS_ORG_FACULTY
from hypha.apply.users.models import Group


class ContractDocumentCategoryAdminForm(WagtailAdminModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.pk:  # New instance, not saved yet
            default_groups = Group.objects.filter(name__in=GROUPS_ORG_FACULTY)
            self.fields["document_access_view"].queryset = default_groups
            self.fields["document_access_view"].initial = default_groups.values_list(
                "pk", flat=True
            )
            self.initial["document_access_view"] = list(
                default_groups.values_list("pk", flat=True)
            )
