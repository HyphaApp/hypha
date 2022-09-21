from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

UserModel = get_user_model()


def get_user_by_email(email):
    qs = UserModel.objects.filter(email__iexact=email)  # case insensitive matching

    # if multiple accounts then check with case sensitive search
    if len(qs) > 1:
        qs = qs.filter(email=email)  # case sensitive matching

    if len(qs) == 0:
        return

    user = qs[0]
    return user


class CustomModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return

        user = get_user_by_email(username)
        if not user:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            UserModel().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
