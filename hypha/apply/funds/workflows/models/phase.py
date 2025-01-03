from django.utils.text import slugify

from ..constants import PHASE_BG_COLORS, UserPermissions
from ..permissions import Permissions


class Phase:
    """
    Phase Names:
    display_name = phase name displayed to staff members in the system
    public_name = phase name displayed to applicants in the system
    future_name = phase_name displayed to applicants if they haven't passed this stage
    """

    def __init__(
        self,
        name,
        display,
        stage,
        permissions,
        step,
        public=None,
        future=None,
        transitions=None,
    ):
        if transitions is None:
            transitions = {}
        self.name = name
        self.display_name = display
        self.display_slug = slugify(display)
        if public and future:
            raise ValueError("Cant provide both a future and a public name")

        self.public_name = public or self.display_name
        self.future_name_staff = future or self.display_name
        self.bg_color = PHASE_BG_COLORS.get(self.display_name, "bg-gray-200")
        self.future_name_public = future or self.public_name
        self.stage = stage
        self.permissions = Permissions(permissions)
        self.step = step

        # For building transition methods on the parent
        self.transitions = {}

        default_permissions = {
            UserPermissions.STAFF,
            UserPermissions.LEAD,
            UserPermissions.ADMIN,
        }

        for transition_target, action in transitions.items():
            transition = {}
            try:
                transition["display"] = action.get("display")
            except AttributeError:
                transition["display"] = action
                transition["permissions"] = default_permissions
            else:
                transition["method"] = action.get("method")
                conditions = action.get("conditions", "")
                transition["conditions"] = conditions.split(",") if conditions else []
                transition["permissions"] = action.get(
                    "permissions", default_permissions
                )
                if "custom" in action:
                    transition["custom"] = action["custom"]

            self.transitions[transition_target] = transition

    def __str__(self):
        return self.display_name

    def __repr__(self):
        return f"<Phase: {self.display_name} ({self.public_name})>"
