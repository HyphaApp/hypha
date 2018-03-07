from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import View

from opentech.apply.users.groups import STAFF_GROUP_NAME


@method_decorator(login_required, name='dispatch')
class ViewDispatcher(View):
    admin_view = None
    applicant_view = None

    def dispatch(self, request, *args, **kwargs):
        if request.user.groups.filter(name=STAFF_GROUP_NAME).exists():
            view = self.admin_view
        else:
            view = self.applicant_view

        return view.as_view()(request, *args, **kwargs)
