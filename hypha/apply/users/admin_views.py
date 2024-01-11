import csv
import os

import django_filters
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import mark_safe
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _
from django.views.decorators.vary import vary_on_headers
from wagtail.admin.auth import any_permission_required
from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.forms.search import SearchForm
from wagtail.compat import AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME
from wagtail.users.views.groups import GroupViewSet, IndexView

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


def create_csv(users_list):
    base_path = os.path.join(settings.PROJECT_DIR, "../media")
    filename = "users.csv"
    with open(os.path.join(base_path + "/" + filename), "w+") as file:
        fieldnames = ["full_name", "email", "status", "role"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for user in users_list:
            writer.writerow(user)
    return base_path + "/" + filename


def export(users):
    users_list = []
    for user in users:
        if user.is_superuser:
            user.roles.insert(0, "Admin")
        roles = ",".join(user.roles)
        user_data = {
            "full_name": user.full_name,
            "email": user.email,
            "status": "Active" if user.is_active else "Inactive",
            "role": roles,
        }
        users_list.append(user_data)
    filepath = create_csv(users_list)
    with open(filepath, "rb") as file:
        response = HttpResponse(file.read(), content_type="text/csv")
        response["Content-Disposition"] = "inline; filename=" + os.path.basename(
            filepath
        )
        return response


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
        fields = ["roles", "status"]

    def filter_by_roles(self, queryset, name, value):
        queryset = queryset.filter(groups__name=value)
        return queryset

    def filter_by_status(self, queryset, name, value):
        if value == "active":
            return queryset.filter(is_active=True)
        elif value == "inactive":
            return queryset.filter(is_active=False)
        return queryset


@any_permission_required(add_user_perm, change_user_perm, delete_user_perm)
@vary_on_headers("X-Requested-With")
def index(request, *args):
    """
    Override wagtail's users index view to filter by full_name
    https://github.com/wagtail/wagtail/blob/af69cb4a544a1b9be1339546be62ff54b389730e/wagtail/users/views/users.py#L47
    """
    q = None
    is_searching = False

    group = None
    group_filter = Q()
    if args:
        group = get_object_or_404(Group, id=args[0])
        group_filter = Q(groups=group) if args else Q()

    model_fields = [f.name for f in User._meta.get_fields()]

    if "q" in request.GET:
        form = SearchForm(request.GET, placeholder=_("Search users"))
        if form.is_valid():
            q = form.cleaned_data["q"]
            is_searching = True
            conditions = Q()

            for term in q.split():
                if "username" in model_fields:
                    conditions |= Q(username__icontains=term)

                if "first_name" in model_fields:
                    conditions |= Q(first_name__icontains=term)

                if "last_name" in model_fields:
                    conditions |= Q(last_name__icontains=term)

                if "email" in model_fields:
                    conditions |= Q(email__icontains=term)

                # filter by full_name
                if "full_name" in model_fields:
                    conditions |= Q(full_name__icontains=term)

            users = User.objects.filter(group_filter & conditions)
    else:
        form = SearchForm(placeholder=_("Search users"))

    if not is_searching:
        users = User.objects.filter(group_filter).order_by("-is_active", "full_name")

    filters = None
    if not group:
        filters = UserFilterSet(request.GET, queryset=users, request=request)
        users = filters.qs

    if "export" in request.GET:
        file = export(users)
        return file

    if "ordering" in request.GET:
        ordering = request.GET["ordering"]

        if ordering == "username":
            users = users.order_by(User.USERNAME_FIELD)
        elif ordering == "status":
            users = users.order_by("is_active")
    else:
        ordering = "name"

    user_count = users.count()
    paginator = Paginator(users.select_related("wagtail_userprofile"), per_page=20)
    users = paginator.get_page(request.GET.get("p"))

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return TemplateResponse(
            request,
            "wagtailusers/users/results.html",
            {
                "users": users,
                "user_count": user_count,
                "is_searching": is_searching,
                "query_string": q,
                "filters": filters,
                "ordering": ordering,
                "app_label": User._meta.app_label,
                "model_name": User._meta.model_name,
            },
        )
    else:
        return TemplateResponse(
            request,
            "wagtailusers/users/index.html",
            {
                "group": group,
                "search_form": form,
                "users": users,
                "user_count": user_count,
                "is_searching": is_searching,
                "ordering": ordering,
                "query_string": q,
                "filters": filters,
                "app_label": User._meta.app_label,
                "model_name": User._meta.model_name,
            },
        )


class CustomGroupIndexView(IndexView):
    """
    Overriding of wagtail.users.views.groups.IndexView to allow for the addition of help text to the displayed group names. This is done utilizing the get_queryset method
    """

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
        return index

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

    @property
    def index_view(self):
        return self.index_view_class.as_view(
            **self.get_index_view_kwargs(),
        )
