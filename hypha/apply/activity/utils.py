import re
from typing import List

from hypha.apply.users.models import User
from hypha.apply.users.roles import ROLES_ORG_FACULTY


def get_mentioned_email_regex(emails: List[str]) -> str:
    return rf"(?:^|(?<=\s))@({'|'.join(re.escape(email) for email in emails)})(?=\s|$)"


def format_comment_mentions(value, user) -> str:
    faculty = User.objects.filter(groups__name__in=ROLES_ORG_FACULTY).distinct()
    email_regex = get_mentioned_email_regex(faculty.values_list("email", flat=True))
    if faculty_matches := re.findall(email_regex, value):
        qs = faculty.filter(email__in=faculty_matches)

        for mention in qs:
            extra_class = " bg-yellow-200" if mention == user else ""
            user_display = f'<span class="font-bold{extra_class}">@{mention.get_display_name()}</span>'
            value = re.sub(
                get_mentioned_email_regex([mention.email]), user_display, value
            )

    return value
