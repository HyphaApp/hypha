"""The payments-flow choice used by ``PROJECTS_PAYMENTS_FLOW``.

Kept dependency-free (no Django imports) so it can be imported from app code
without triggering settings cycles; settings modules set the value as a plain
string. ``PaymentsFlow`` subclasses ``str`` so members compare equal to
their string values and work directly in template ``{% if %}`` comparisons.

"""

from enum import Enum


class PaymentsFlow(str, Enum):
    INVOICING = "INVOICING"
    DISBURSEMENTS = "DISBURSEMENTS"
    DISABLED = "DISABLED"
