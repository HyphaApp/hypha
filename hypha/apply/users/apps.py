from django.apps import AppConfig

# from hypha.apply.users.models import User


class UsersConfig(AppConfig):
    name = "hypha.apply.users"

    def ready(self):
        # Connect the attachment deletion handler
        pass
