from .api_base import ApiBase


class Invoice(ApiBase):
    """Class to create Contract Invoice Release at Sage IntAcct."""

    def post(self, data: dict):
        data = {"create_potransaction": data}
        return self.format_and_send_request(data)
