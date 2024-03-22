import django_filters
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import CharField, Q, Value
from django.db.models.functions import Coalesce, Lower, NullIf
from django.template.defaultfilters import mark_safe
from wagtail.admin.filters import WagtailFilterSet
from wagtail.compat import AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME
from wagtail.users.views.groups import GroupViewSet
from wagtail.users.views.groups import IndexView as GroupIndexView
from wagtail.users.views.users import Index as UserIndexView
from wagtail.users.views.users import get_users_filter_query

from .models import GroupDesc

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
        ("inactive", "INACTIVE"),
        ("active", "ACTIVE"),
    )
    roles = django_filters.ModelChoiceFilter(
        queryset=Group.objects.all(), label="Roles", method="filter_by_roles"
    )
    status = django_filters.ChoiceFilter(
        choices=STATUS_CHOICES, label="Status", method="filter_by_status"
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
    """
    Override wagtail's users index view to filter by full_name. This view
    also allows for the addition of custom fields to the list_export
    and list filtering.
    """

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

    default_ordering = "name"
    list_filter = ("is_active",)

    filterset_class = UserFilterSet

    def get_context_data(self, *args, object_list=None, **kwargs):
        ctx = super().get_context_data(*args, object_list=object_list, **kwargs)
        ctx["filters"] = self.get_filterset_class()(
            self.request.GET, queryset=self.get_queryset(), request=self.request
        )
        return ctx

    def get_queryset(self):
        """
        Override the original queryset to filter by full_name, mostly copied from
        super().get_queryset() with the addition of the custom code
        """
        model_fields = set(self.model_fields)
        if self.is_searching:
            conditions = get_users_filter_query(self.search_query, model_fields)

            # == custom code
            for term in self.search_query.split():
                if "full_name" in model_fields:
                    conditions |= Q(full_name__icontains=term)
            # == custom code end

            users = User.objects.filter(self.group_filter & conditions)
        else:
            users = User.objects.filter(self.group_filter)

        if self.locale:
            users = users.filter(locale=self.locale)

        users = users.annotate(
            display_name=Coalesce(
                NullIf("full_name", Value("")), "email", output_field=CharField()
            ),
        )

        if "wagtail_userprofile" in model_fields:
            users = users.select_related("wagtail_userprofile")

        # == custom code
        if "full_name" in model_fields:
            users = users.order_by(Lower("display_name"))
        # == custom code end

        if self.get_ordering() == "username":
            users = users.order_by(User.USERNAME_FIELD)

        if self.get_ordering() == "name":
            users = users.order_by(Lower("display_name"))

        # == custom code
        if not self.group:
            filterset_class = self.get_filterset_class()
            users = filterset_class(
                self.request.GET, queryset=users, request=self.request
            ).qs
        # == end custom code

        return users


class CustomGroupIndexView(GroupIndexView):
    """
    Overriding of wagtail.users.views.groups.IndexView to allow for the addition of help text to the displayed group names. This is done utilizing the get_queryset method
    """

    model = Group

    def get_queryset(self):
        """
        Overriding the normal queryset that would return all Group objects, this returnd an iterable of groups with custom names containing HTML help text.
        """
        group_qs = super().get_queryset()

        custom_groups = []

        for group in group_qs:
            help_text = GroupDesc.get_from_group(group)
            if help_text:
                group.name = mark_safe(
                    f"{group.name}<p class=group-help-text>{help_text}</p>"
                )

            custom_groups.append(group)

        return custom_groups


class CustomGroupViewSet(GroupViewSet):
    """
    Overriding the wagtail.users.views.groups.GroupViewSet just to use custom users view(index)
    when getting all users for a group.
    """

    index_view_class = CustomGroupIndexView

    @property
    def users_view(self):
        return CustomUserIndexView.as_view()

    @property
    def users_results_view(self):
        return CustomUserIndexView.as_view(results_only=True)

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
