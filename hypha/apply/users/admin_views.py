import django_filters
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import CharField, Value
from django.db.models.functions import Coalesce, Lower, NullIf
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import gettext, gettext_lazy
from rolepermissions import roles
from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.ui.tables import (
    BulkActionsCheckboxColumn,
    Column,
    DateColumn,
    StatusTagColumn,
)
from wagtail.admin.utils import get_user_display_name, set_query_params
from wagtail.admin.widgets.button import HeaderButton
from wagtail.compat import AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME
from wagtail.users.views.groups import EditView as GroupEditView
from wagtail.users.views.groups import GroupViewSet as WagtailGroupViewSet
from wagtail.users.views.groups import IndexView as GroupIndexView
from wagtail.users.views.users import IndexView as UserIndexView
from wagtail.users.views.users import UserColumn
from wagtail.users.views.users import UserViewSet as WagtailUserViewSet

from .forms import CustomUserCreationForm, CustomUserEditForm

User = get_user_model()

# Typically we would check the permission 'auth.change_user' (and 'auth.add_user' /
# 'auth.delete_user') for user management actions, but this may vary according to
# the AUTH_USER_MODEL setting
add_user_perm = "{0}.add_{1}".format(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower())
change_user_perm = "{0}.change_{1}".format(
    AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower()
)
delete_user_perm = "{0}.delete_{1}".format(
    AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower()
)


class UserFilterSet(WagtailFilterSet):
    STATUS_CHOICES = (
        ("inactive", gettext_lazy("INACTIVE")),
        ("active", gettext_lazy("ACTIVE")),
    )
    roles = django_filters.ModelChoiceFilter(
        queryset=Group.objects.all(),
        label=gettext_lazy("Roles"),
        method="filter_by_roles",
    )
    status = django_filters.ChoiceFilter(
        choices=STATUS_CHOICES, label=gettext_lazy("Status"), method="filter_by_status"
    )

    class Meta:
        model = User
        fields = ["roles", "status", "is_superuser"]

    def filter_by_roles(self, queryset, name, value):
        queryset = queryset.filter(groups__name=value)
        return queryset

    def filter_by_status(self, queryset, name, value):
        if value == "active":
            return queryset.filter(is_active=True)
        elif value == "inactive":
            return queryset.filter(is_active=False)
        return queryset


class CustomUserIndexView(UserIndexView):
    list_export = [
        "email",
        "full_name",
        "slack",
        "roles",
        "is_superuser",
        "is_active",
        "date_joined",
        "last_login",
    ]

    @cached_property
    def columns(self):
        # Override to add roles column
        _UserColumn = self._get_title_column_class(UserColumn)
        return [
            BulkActionsCheckboxColumn("bulk_actions", obj_type="user"),
            _UserColumn(
                "name",
                accessor=lambda u: get_user_display_name(u),
                label=gettext_lazy("Name"),
                get_url=self.get_edit_url,
                classname="name",
            ),
            Column(
                self.model.USERNAME_FIELD,
                accessor="get_username",
                label=gettext_lazy("Username"),
                sort_key=self.model.USERNAME_FIELD,
                classname="username",
                width="20%",
            ),
            Column(
                "is_superuser",
                accessor=lambda u: gettext_lazy("Admin") if u.is_superuser else None,
                label=gettext_lazy("Access level"),
                sort_key="is_superuser",
                classname="level",
                width="10%",
            ),
            Column(
                "roles",
                accessor=lambda u: ", ".join(u.roles),
                label=gettext_lazy("Roles"),
                classname="level",
                width="10%",
            ),
            StatusTagColumn(
                "is_active",
                accessor=lambda u: (
                    gettext_lazy("Active") if u.is_active else gettext_lazy("Inactive")
                ),
                primary=lambda u: u.is_active,
                label=gettext_lazy("Status"),
                sort_key="is_active" if "is_active" in self.model_fields else None,
                classname="status",
                width="10%",
            ),
            DateColumn(
                "last_login",
                label=gettext_lazy("Last login"),
                sort_key="last_login",
                classname="last-login",
                width="10%",
            ),
        ]

    def get_base_queryset(self):
        users = User._default_manager.all()

        users = users.annotate(
            display_name=Coalesce(
                NullIf("full_name", Value("")), "email", output_field=CharField()
            ),
        )

        if "wagtail_userprofile" in self.model_fields:
            users = users.select_related("wagtail_userprofile")

        return users

    def order_queryset(self, queryset):
        if self.ordering == "name":
            return queryset.order_by(Lower("display_name"))
        if self.ordering == "-name":
            return queryset.order_by(Lower("display_name"))
        return super().order_queryset(queryset)


class CustomUserViewSet(WagtailUserViewSet):
    filterset_class = UserFilterSet
    index_view_class = CustomUserIndexView

    def get_form_class(self, for_update=False):
        if for_update:
            return CustomUserEditForm
        return CustomUserCreationForm


class CustomGroupIndexView(GroupIndexView):
    """
    Overriding of wagtail.users.views.groups.IndexView to allow for the addition of help text to the displayed group names. This is done utilizing the get_queryset method
    """

    model = Group

    def get_queryset(self):
        """
        Overriding the normal queryset that would return all Group objects, this returned an iterable of groups with custom names containing HTML help text.
        """
        group_qs = super().get_queryset()

        custom_groups = []

        for group in group_qs:
            # Check if the group is a role
            help_text = getattr(
                roles.registered_roles.get(group.name, {}), "help_text", ""
            )
            if help_text:
                group.name = mark_safe(
                    f"{group.name}<p class=group-help-text>{help_text}</p>"
                )

            custom_groups.append(group)

        return custom_groups


class CustomGroupEditView(GroupEditView):
    @cached_property
    def header_buttons(self):
        return [
            HeaderButton(
                gettext("View users in this group"),
                url=set_query_params(
                    reverse("wagtailusers_users:index"),
                    {"roles": self.object.pk},
                ),
                icon_name="user",
            )
        ]


class CustomGroupViewSet(WagtailGroupViewSet):
    """
    Overriding the wagtail.users.views.groups.GroupViewSet just to use custom users view(index)
    when getting all users for a group.
    """

    index_view_class = CustomGroupIndexView
    edit_view_class = CustomGroupEditView

    @property
    def users_view(self):
        return CustomUserIndexView.as_view()

    @property
    def users_results_view(self):
        return CustomUserIndexView.as_view(results_only=True)

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
