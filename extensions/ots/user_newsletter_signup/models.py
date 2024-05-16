from django.db import models

# from hypha.apply.users.forms import ProfileForm
from hypha.apply.users.models import User

User.add_to_class("newsletter_signup", models.BooleanField(default=True))
