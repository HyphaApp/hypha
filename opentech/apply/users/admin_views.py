from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers

from wagtail.admin.forms.search import SearchForm
from wagtail.admin.utils import any_permission_required
from wagtail.core.compat import AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME

User = get_user_model()

# Typically we would check the permission 'auth.change_user' (and 'auth.add_user' /
# 'auth.delete_user') for user management actions, but this may vary according to
# the AUTH_USER_MODEL setting
add_user_perm = "{0}.add_{1}".format(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower())
change_user_perm = "{0}.change_{1}".format(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower())
delete_user_perm = "{0}.delete_{1}".format(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower())


@any_permission_required(add_user_perm, change_user_perm, delete_user_perm)
@vary_on_headers('X-Requested-With')
def index(request):
    """
    Override wagtail's users index view to filter by full_name
    https://github.com/wagtail/wagtail/blob/af69cb4a544a1b9be1339546be62ff54b389730e/wagtail/users/views/users.py#L47
    """
    q = None
    is_searching = False

    model_fields = [f.name for f in User._meta.get_fields()]

    if 'q' in request.GET:
        form = SearchForm(request.GET, placeholder=_("Search users"))
        if form.is_valid():
            q = form.cleaned_data['q']
            is_searching = True
            conditions = Q()

            for term in q.split():
                if 'username' in model_fields:
                    conditions |= Q(username__icontains=term)

                if 'first_name' in model_fields:
                    conditions |= Q(first_name__icontains=term)

                if 'last_name' in model_fields:
                    conditions |= Q(last_name__icontains=term)

                if 'email' in model_fields:
                    conditions |= Q(email__icontains=term)

                # filter by full_name
                if 'full_name' in model_fields:
                    conditions |= Q(full_name__icontains=term)

            users = User.objects.filter(conditions)
    else:
        form = SearchForm(placeholder=_("Search users"))

    if not is_searching:
        users = User.objects.all()

    if 'last_name' in model_fields and 'first_name' in model_fields:
        users = users.order_by('last_name', 'first_name')

    if 'ordering' in request.GET:
        ordering = request.GET['ordering']

        if ordering == 'username':
            users = users.order_by(User.USERNAME_FIELD)
    else:
        ordering = 'name'

    paginator = Paginator(users, per_page=20)
    users = paginator.get_page(request.GET.get('p'))

    if request.is_ajax():
        return render(request, "wagtailusers/users/results.html", {
            'users': users,
            'is_searching': is_searching,
            'query_string': q,
            'ordering': ordering,
        })
    else:
        return render(request, "wagtailusers/users/index.html", {
            'search_form': form,
            'users': users,
            'is_searching': is_searching,
            'ordering': ordering,
            'query_string': q,
        })
