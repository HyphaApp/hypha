import os
import uuid
from typing import List, Optional, Tuple

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Case, Q, QuerySet, Value, When
from django.db.models.functions import Concat
from django.urls import reverse
from django.utils import timezone
from django.utils.text import get_valid_filename
from django.utils.translation import gettext as _

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
PARTNER = _("partners")
ALL = _("all")
APPLICANT_PARTNERS = f"{APPLICANT} {PARTNER}"

# Visibility choice strings
VISIBILITY = {
    APPLICANT: _("Applicants"),
    TEAM: _("Staff only"),
    REVIEWER: _("Reviewers"),
    PARTNER: _("Partners"),
    ALL: _("All"),
    APPLICANT_PARTNERS: _("Applicants & Partners"),
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

        # There are scenarios where users will have activities in which they
        # wouldn't have visibility just using Activity.visibility_for. Thus,
        # the queryset should include activity in which they author
        # (ie. A comment made only to staff from a partner).
        if user.is_applicant:
            return self.exclude(message=messages.get(MESSAGES.NEW_REVIEW)).filter(
                Q(visibility__in=self.model.visibility_for(user)) | Q(user=user)
            )

        return self.filter(
            Q(visibility__in=self.model.visibility_for(user)) | Q(user=user)
        )

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

    message = models.TextField()
    visibility = models.CharField(
        choices=list(VISIBILITY.items()), default=APPLICANT, max_length=30
    )

    # Fields for handling versioning of the comment activity models
    edited = models.DateTimeField(default=None, null=True)
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

    @property
    def priviledged(self):
        # Not visible to applicant
        return self.visibility not in [APPLICANT, ALL]

    @property
    def private(self):
        # not visible to all
        return self.visibility not in [ALL]

    def __str__(self):
        return '{}: for "{}"'.format(self.get_type_display(), self.source)

    @classmethod
    def visibility_for(cls, user) -> List[str]:
        """Gets activity visibility for a specified user

        Args:
            user:
                [`User`][hypha.apply.users.models.User] to get visibility for

        Returns:
            A list of visibility strings
        """
        if user.is_apply_staff:
            return [TEAM, APPLICANT, REVIEWER, APPLICANT_PARTNERS, PARTNER, ALL]
        if user.is_reviewer:
            return [REVIEWER, ALL]
        if user.is_finance or user.is_contracting:
            # for project part
            return [TEAM, APPLICANT, REVIEWER, PARTNER, ALL]
        if user.is_applicant:
            return [APPLICANT, ALL, APPLICANT_PARTNERS]
        if user.is_partner:
            return [PARTNER, ALL, APPLICANT_PARTNERS]

        return [ALL]

    @classmethod
    def visibility_choices_for(
        cls, user, submission_partner_list: Optional[QuerySet] = None
    ) -> List[Tuple[str, str]]:
        """Gets activity visibility choices for the specified user

        Uses the given user (and partner query set if provided) to give
        the specified user activity visibility choices.

        Args:
            user:
                The [`User`][hypha.apply.users.models.User] being given
                visibility choices
            submission_has_partner:
                An optional QuerySet of partners
                ([`Users`][hypha.apply.users.models.User])
        Returns:
            A list of tuples in the format of:
            [(<visibility string>, <visibility display string>), ...]
        """
        has_partner = submission_partner_list and len(submission_partner_list) > 0

        if user.is_apply_staff:
            if not has_partner:
                choices = [
                    (TEAM, VISIBILITY[TEAM]),
                    (APPLICANT, VISIBILITY[APPLICANT]),
                    (REVIEWER, VISIBILITY[REVIEWER]),
                    (ALL, VISIBILITY[ALL]),
                ]
            else:
                choices = [
                    (TEAM, VISIBILITY[TEAM]),
                    (APPLICANT, VISIBILITY[APPLICANT]),
                    (PARTNER, VISIBILITY[PARTNER]),
                    (APPLICANT_PARTNERS, VISIBILITY[APPLICANT_PARTNERS]),
                    (REVIEWER, VISIBILITY[REVIEWER]),
                    (ALL, VISIBILITY[ALL]),
                ]
            return choices

        if user.is_partner and has_partner and submission_partner_list.contains(user):
            return [
                (APPLICANT_PARTNERS, VISIBILITY[APPLICANT_PARTNERS]),
                (PARTNER, VISIBILITY[PARTNER]),
                (TEAM, VISIBILITY[TEAM]),
            ]

        if user.is_applicant and has_partner:
            return [
                (APPLICANT_PARTNERS, VISIBILITY[PARTNER]),
                (APPLICANT, VISIBILITY[TEAM]),
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

    def __str__(self):
        if self.source and hasattr(self.source, "title"):
            return f"{self.by} {self.get_type_display()} - {self.source.title }"
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
