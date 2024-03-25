"""
Sage Intacct contract
"""

from .api_base import ApiBase


class Project(ApiBase):
    """Class for contract APIs."""

    def __init__(self):
        ApiBase.__init__(self, dimension="PODOCUMENT")
