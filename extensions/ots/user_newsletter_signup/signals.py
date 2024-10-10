from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from hypha.apply.users.models import User


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, update_fields, **kwargs):
    if created:
        if instance.newsletter_signup:
            print("User added with newsletter being signed up!")


@receiver(pre_save, sender=User)
def user_pre_save(sender, instance, update_fields, **kwargs):
    if (
        instance.id
        and User.objects.get(id=instance.id).newsletter_signup
        != instance.newsletter_signup
    ):
        if instance.newsletter_signup:
            print("Someone is opting in to the newsletter signup")
        else:
            print("Someone is opting out of the newsletter signup!")
