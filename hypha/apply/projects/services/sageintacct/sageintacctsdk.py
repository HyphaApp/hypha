from .wrapper import ApiBase, Purchasing


class SageIntacctSDK:
    """
    Sage Intacct SDK
    """

    def __init__(
        self, sender_id: str, sender_password: str,
        user_id: str, company_id: str, user_password: str,
        entity_id: str = None
    ):
        """
        Initialize connection to Sage Intacct
        :param sender_id: Sage Intacct sender id
        :param sender_password: Sage Intacct sener password
        :param user_id: Sage Intacct user id
        :param company_id: Sage Intacct company id
        :param user_password: Sage Intacct user password
        :param (optional) entity_id: Sage Intacct entity ID
        """
        # Initializing variables
        self.__sender_id = sender_id
        self.__sender_password = sender_password
        self.__user_id = user_id
        self.__company_id = company_id
        self.__user_password = user_password
        self.__entity_id = entity_id

        self.api_base = ApiBase()
        self.purchasing = Purchasing()
        self.update_sender_id()
        self.update_sender_password()
        self.update_session_id()

    def update_sender_id(self):
        """
        Update the sender id in all API objects.
        """
        self.api_base.set_sender_id(self.__sender_id)
        self.purchasing.set_sender_id(self.__sender_id)

    def update_sender_password(self):
        """
        Update the sender password in all API objects.
        """
        self.api_base.set_sender_password(self.__sender_password)
        self.purchasing.set_sender_password(self.__sender_password)

    def update_session_id(self):
        """
        Update the session id and change it in all API objects.
        """
        self.__session_id = self.api_base.get_session_id(
            self.__user_id,
            self.__company_id,
            self.__user_password,
            self.__entity_id
        )
        self.api_base.set_session_id(self.__session_id)
        self.purchasing.set_session_id(self.__session_id)
