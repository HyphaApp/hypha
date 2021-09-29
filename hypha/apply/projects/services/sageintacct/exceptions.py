class SageIntacctSDKError(Exception):
    """The base exception class for SageIntacctSDK.

    Parameters:
        msg (str): Short description of the error.
        response: Error response from the API call.
    """

    def __init__(self, msg, response=None):
        super(SageIntacctSDKError, self).__init__(msg)
        self.message = msg
        self.response = response

    def __str__(self):
        return repr(self.message)


class SageIntacctSDKWarning(Warning):
    """The base Warning class for SageIntacctSDK.

       Parameters:
           msg (str): Short description of the alert.
           response: Error response from the API call.
       """

    def __init__(self, msg, response=None):
        super(SageIntacctSDKWarning, self).__init__(msg)
        self.message = msg
        self.response = response

    def __str__(self):
        return repr(self.message)


class ExpiredTokenError(SageIntacctSDKError):
    """Expired (old) access token, 498 error."""


class InvalidTokenError(SageIntacctSDKError):
    """Wrong/non-existing access token, 401 error."""


class NoPrivilegeError(SageIntacctSDKError):
    """The user has insufficient privilege, 403 error."""


class WrongParamsError(SageIntacctSDKError):
    """Some of the parameters (HTTP params or request body) are wrong, 400 error."""


class NotFoundItemError(SageIntacctSDKError):
    """Not found the item from URL, 404 error."""


class InternalServerError(SageIntacctSDKError):
    """The rest SageIntacctSDK errors, 500 error."""


# WARNING SECTION
class DataIntegrityWarning(SageIntacctSDKWarning):
    """Warns the user that a query did not return all records meeting specified criteria"""
