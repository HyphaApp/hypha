# User permissions and their defaults

### User types

1. `Staff`
2. `Applicant`
3. `Reviewer`
4. `Partner`
5. `Community`

### User roles

1. `STAFF`
2. `ADMIN`
3. `LEAD`
4. `APPLICANT`

User roles are defined in an enumerated class `UserPermissions` in `workflow.py`.

Permission settings are created through a helper function `create_permissions` that takes a parameter of `permissions`, a dict that has the following keys: `can_do`, `can_edit`, `can_review`, and `can_view` are defined by a list containing the user roles that can perform those actions.

### Pre-defined permission settings

`no_permissions` — view only permissions for all user roles. will return

    {
    ‘edit’: [],
    ‘review’: [],
    ‘view’: [staff_can, applicant_can, reviewer_can, partner_can,],
    }

`default_permissions` — only `staff` user roles can edit or review. All other user types i.e. `staff`, `applicant`, `reviewer`, and `partner` are view-only.

`hidden_from_applicant_permissions` — only `staff` user roles can edit or review. Only `staff` or `reviewer` user roles can view. Hidden from `applicant` and `partner`

`reviewer_review_permissions` — only `staff` can edit. Only `staff` and `reviewer` can review. All user types can view.

`community_review_permissions` — only `staff` can edit. Only `staff`, `reviewer` or `community` can review. All user types can view.

`applicant_edit_permissions` — only `applicant` and `partner` can edit. `staff` can review. All user types can view.

`staff_edit_permissions` — only `staff` can edit. Default permissions for other values. no user type will have permissions to review. All user types can view.
