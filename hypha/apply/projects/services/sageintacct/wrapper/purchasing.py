
"""
Sage Intacct purchasing
"""
from .api_base import ApiBase


class Purchasing(ApiBase):
    """Class for Purchasing APIs."""
    def __init__(self):
        ApiBase.__init__(self, dimension='PODOCUMENTENTRY')
