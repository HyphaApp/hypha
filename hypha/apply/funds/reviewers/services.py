from django.contrib.auth import get_user_model
from django.db.models import Q
from django.db.models.query import QuerySet

from hypha.apply.users.roles import STAFF_GROUP_NAME

User = get_user_model()


def get_all_reviewers(*args, **kwargs) -> QuerySet:
    """All assigned reviewers, staff or admin."""
    q_obj = (
        Q(submissions_reviewer__isnull=False)
        | Q(groups__name=STAFF_GROUP_NAME)
        | Q(is_superuser=True)
    )
    return User.objects.filter(q_obj).distinct()
