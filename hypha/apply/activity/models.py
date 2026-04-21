import os
import uuid
from typing import List, Optional, Tuple

from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Case, Q, Value, When
from django.db.models.functions import Concat
from django.urls import reverse
from django.utils import timezone
from django.utils.text import get_valid_filename
from django.utils.translation import gettext_lazy as _

from hypha.apply.utils.storage import PrivateStorage

from .options import MESSAGES

COMMENT = "comment"
ACTION = "action"

ACTIVITY_TYPES = {
    COMMENT: _("Comment"),
    ACTION: _("Action"),
}

# Visibility strings. Used to determine visibility states but are also
# sometimes shown to users.
# (ie. hypha.apply.activity.templatetags.activity_tags.py)
APPLICANT = _("applicant")
TEAM = _("team")
REVIEWER = _("reviewers")
ALL = _("all")

# Visibility choice strings
VISIBILITY = {
    APPLICANT: _("Applicants"),
    TEAM: _("Staff only"),
    REVIEWER: _("Reviewers"),
    ALL: _("All"),
}


class BaseActivityQuerySet(models.QuerySet):
    def visible_to(self, user) -> models.QuerySet:
        """Get a QuerySet of all items that are visible to the given user.

        Args:
            user:
                [`User`][hypha.apply.users.models.User] to filter visibility of

        Returns:
            A QuerySet containing all items visible to the specified user
        """

        # To hide reviews from the applicant's activity feed
        # Todo: It is just for historic data and not be needed for new data after this.
        from .messaging import ActivityAdapter

        messages = ActivityAdapter.messages

        user_qs = Q(user=user)

        if user.is_applicant:
            # Handle the edge case where a reviewer is also an
            # applicant. Ensures that any applications/projects the user
            # authored will have comment visibility of applicant while others
            # will get the appropriate role.
            if user.is_reviewer:
                ApplicationSubmission = apps.get_model("funds", "ApplicationSubmission")
                Project = apps.get_model("application_projects", "Project")

                app_content_type = ContentType.objects.get_for_model(
                    ApplicationSubmission
                )
                proj_content_type = ContentType.objects.get_for_model(Project)

                authored_apps = ApplicationSubmission.objects.filter(user_qs).values(
                    "id"
                )
                authored_projs = Project.objects.filter(user_qs).values("id")

                proj_app_qs = (
                    Q(source_content_type=app_content_type)
                    & Q(source_object_id__in=authored_apps)
                ) | (
                    Q(source_content_type=proj_content_type)
                    & Q(source_object_id__in=authored_projs)
                )

                # Activities the user is the author of the source submission
                applicant_activity = self.filter(
                    proj_app_qs
                    & Q(
                        Q(visibility__in=self.model.visibility_for(user, True))
                        | user_qs
                    )
                )
                # All other activities
                other_activity = self.exclude(
                    Q(message=messages.get(MESSAGES.NEW_REVIEW)) | proj_app_qs
                ).filter(Q(visibility__in=self.model.visibility_for(user)) | user_qs)
                return applicant_activity | other_activity
            else:
                return self.exclude(message=messages.get(MESSAGES.NEW_REVIEW)).filter(
                    Q(visibility__in=self.model.visibility_for(user)) | user_qs
                )

        return self.filter(Q(visibility__in=self.model.visibility_for(user)) | user_qs)

    def newer(self, activity):
        return self.filter(timestamp__gt=activity.timestamp)


class ActivityQuerySet(BaseActivityQuerySet):
    def comments(self):
        return self.filter(type=COMMENT)

    def actions(self):
        return self.filter(type=ACTION)

    def latest(self):
        return self.filter(
            timestamp__gte=(timezone.now() - timezone.timedelta(days=30))
        )


class ActivityBaseManager(models.Manager):
    def create(self, **kwargs):
        kwargs.update(type=self.type)
        return super().create(**kwargs)

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                type=self.type,
                current=True,
            )
        )


class CommentQueryset(BaseActivityQuerySet):
    pass


class CommentManger(ActivityBaseManager):
    type = COMMENT


class ActionQueryset(BaseActivityQuerySet):
    pass


class ActionManager(ActivityBaseManager):
    type = ACTION


def get_attachment_upload_path(instance, filename):
    return f"activity/attachments/{instance.id}/{get_valid_filename(filename)}"


class ActivityAttachment(models.Model):
    wagtail_reference_index_ignore = True

    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    activity = models.ForeignKey(
        "Activity", on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(
        upload_to=get_attachment_upload_path, storage=PrivateStorage()
    )

    class Meta:
        verbose_name = _("activity attachment")
        verbose_name_plural = _("activity attachments")

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    def __str__(self):
        return self.filename

    def get_absolute_url(self):
        return reverse("activity:attachment", kwargs={"file_pk": str(self.uuid)})


class Activity(models.Model):
    timestamp = models.DateTimeField()
    type = models.CharField(choices=ACTIVITY_TYPES.items(), max_length=30)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    source_content_type = models.ForeignKey(
        ContentType,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="activity_source",
    )
    source_object_id = models.PositiveIntegerField(blank=True, null=True, db_index=True)
    source = GenericForeignKey("source_content_type", "source_object_id")

    message = models.TextField(_("message"))
    visibility = models.CharField(
        _("visibility"),
        choices=list(VISIBILITY.items()),
        default=APPLICANT,
        max_length=30,
    )

    # Fields for handling versioning of the comment activity models
    edited = models.DateTimeField(default=None, null=True)
    deleted = models.DateTimeField(default=None, null=True)
    current = models.BooleanField(default=True)
    previous = models.ForeignKey("self", on_delete=models.CASCADE, null=True)

    # Fields for generic relations to other objects. related_object should implement `get_absolute_url`
    related_content_type = models.ForeignKey(
        ContentType,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="activity_related",
    )
    related_object_id = models.PositiveIntegerField(blank=True, null=True)
    related_object = GenericForeignKey("related_content_type", "related_object_id")

    objects = models.Manager.from_queryset(ActivityQuerySet)()
    comments = CommentManger.from_queryset(CommentQueryset)()
    actions = ActionManager.from_queryset(ActionQueryset)()

    wagtail_reference_index_ignore = True

    class Meta:
        ordering = ["-timestamp"]
        base_manager_name = "objects"
        verbose_name = _("activity")
        verbose_name_plural = _("activities")

    def get_absolute_url(self):
        # coverup for both submission and project as source.
        submission_id = (
            self.source.submission_id
            if hasattr(self.source, "submission")
            else self.source.id
        )
        return f"{reverse('funds:submissions:comments', args=[submission_id])}#communications--{self.id}"

    @property
    def privileged(self):
        # Not visible to applicant
        return self.visibility not in [APPLICANT, ALL]

    @property
    def private(self):
        # not visible to all
        return self.visibility not in [ALL]

    def __str__(self):
        return '{}: for "{}"'.format(self.get_type_display(), self.source)

    @classmethod
    def visibility_for(
        cls, user, is_submission_author: Optional[bool] = False
    ) -> List[str]:
        """Gets activity visibility for a specified user

        Takes an optional boolean that is used to determine the visibility of
        an application comment.

        Args:
            user:
                [`User`][hypha.apply.users.models.User] to get visibility for
            is_submission_author:
                boolean used when the `user` is the applicant of the source activity

        Returns:
            A list of visibility strings
        """
        if user.is_apply_staff or user.is_finance or user.is_contracting:
            return [TEAM, APPLICANT, REVIEWER, ALL]
        if user.is_reviewer and not is_submission_author:
            return [REVIEWER, ALL]
        if user.is_applicant:
            return [APPLICANT, ALL]

        return [ALL]

    @classmethod
    def visibility_choices_for(cls, user) -> List[Tuple[str, str]]:
        """Gets activity visibility choices for the specified user

        Args:
            user: The [`User`][hypha.apply.users.models.User] being given visibility choices

        Returns:
            A list of tuples in the format of:
            [(<visibility string>, <visibility display string>), ...]
        """

        if user.is_apply_staff:
            return [
                (TEAM, VISIBILITY[TEAM]),
                (APPLICANT, VISIBILITY[APPLICANT]),
                (REVIEWER, VISIBILITY[REVIEWER]),
                (ALL, VISIBILITY[ALL]),
            ]

        if user.is_applicant:
            return [(APPLICANT, VISIBILITY[APPLICANT])]

        if user.is_reviewer:
            return [(REVIEWER, VISIBILITY[REVIEWER])]

        if user.is_finance or user.is_contracting:
            return [(TEAM, VISIBILITY[TEAM]), (APPLICANT, VISIBILITY[APPLICANT])]

        return [(ALL, VISIBILITY[ALL])]


class Event(models.Model):
    """Model to track when messages are triggered"""

    wagtail_reference_index_ignore = True

    when = models.DateTimeField(auto_now_add=True)
    type = models.CharField(_("verb"), choices=MESSAGES.choices, max_length=50)
    by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True
    )
    content_type = models.ForeignKey(
        ContentType, blank=True, null=True, on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField(blank=True, null=True)
    source = GenericForeignKey("content_type", "object_id")

    class Meta:
        verbose_name = _("event")
        verbose_name_plural = _("events")

    def __str__(self):
        if self.source and hasattr(self.source, "title"):
            return f"{self.by} {self.get_type_display()} - {self.source.title}"
        else:
            return f"{self.by} {self.get_type_display()}"


class MessagesQueryset(models.QuerySet):
    def update_status(self, status):
        if status:
            return self.update(
                status=Case(
                    When(status="", then=Value(status)),
                    default=Concat("status", Value("<br />" + status)),
                    output_field=models.TextField(),
                ),
            )

    update_status.queryset_only = True


class Message(models.Model):
    """Model to track content of messages sent from an event"""

    type = models.CharField(max_length=15)
    content = models.TextField()
    recipient = models.CharField(max_length=250)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    status = models.TextField()
    external_id = models.CharField(
        max_length=75, null=True, blank=True
    )  # Stores the id of the object from an external system
    sent_in_email_digest = models.BooleanField(default=False)
    objects = MessagesQueryset.as_manager()

    class Meta:
        verbose_name = _("message")
        verbose_name_plural = _("messages")

    def __str__(self):
        return f"[{self.type}][{self.status}] {self.content}"

    def update_status(self, status):
        if status:
            self.status = Case(
                When(status="", then=Value(status)),
                default=Concat("status", Value("<br />" + status)),
                output_field=models.TextField(),
            )
            self.save()
