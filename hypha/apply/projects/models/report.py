import datetime
import os

from dateutil.relativedelta import relativedelta
from django.apps import apps
from django.conf import settings
from django.contrib.humanize.templatetags.humanize import ordinal
from django.db import models
from django.db.models import Case, ExpressionWrapper, F, OuterRef, Q, Subquery, When
from django.db.models.functions import Cast
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from wagtail.fields import StreamField

from hypha.apply.funds.models.mixins import AccessFormData
from hypha.apply.projects.blocks import ProjectFormCustomFormFieldsBlock
from hypha.apply.stream_forms.files import StreamFieldDataEncoder
from hypha.apply.stream_forms.models import BaseStreamForm
from hypha.apply.utils.storage import PrivateStorage


def report_path(instance, filename):
    return (
        f"reports/{instance.report.report_id}/version/{instance.report_id}/{filename}"
    )


class ReportQueryset(models.QuerySet):
    def done(self):
        return self.filter(
            Q(current__isnull=False) | Q(skipped=True),
        )

    def to_do(self):
        today = timezone.now().date()
        return self.filter(
            current__isnull=True,
            skipped=False,
            end_date__lt=today,
        ).order_by("end_date")

    def any_very_late(self):
        two_weeks_ago = timezone.now().date() - relativedelta(weeks=2)
        return self.to_do().filter(end_date__lte=two_weeks_ago)

    def submitted(self):
        return self.filter(current__isnull=False)

    def for_table(self):
        Project = apps.get_model("application_projects", "Project")
        return self.annotate(
            last_end_date=Subquery(
                Report.objects.filter(
                    project=OuterRef("project_id"), end_date__lt=OuterRef("end_date")
                ).values("end_date")[:1]
            ),
            project_start_date=Subquery(
                Project.objects.filter(
                    pk=OuterRef("project_id"),
                )
                .with_start_date()
                .values("start")[:1]
            ),
            start=Case(
                When(
                    last_end_date__isnull=False,
                    # Expression Wrapper doesn't cast the calculated object
                    # Use cast to get an actual date object
                    then=Cast(
                        ExpressionWrapper(
                            F("last_end_date") + datetime.timedelta(days=1),
                            output_field=models.DateTimeField(),
                        ),
                        models.DateField(),
                    ),
                ),
                default=F("project_start_date"),
                output_field=models.DateField(),
            ),
        )


class Report(BaseStreamForm, AccessFormData, models.Model):
    skipped = models.BooleanField(default=False)
    end_date = models.DateField()
    project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="reports"
    )
    form_fields = StreamField(
        # Re-use the Project Custom Form class. The original fields (used at the time of response) should be required.
        ProjectFormCustomFormFieldsBlock(),
        use_json_field=True,
        null=True,
    )
    form_data = models.JSONField(encoder=StreamFieldDataEncoder, default=dict)
    submitted = models.DateTimeField(null=True)
    notified = models.DateTimeField(null=True)
    current = models.OneToOneField(
        "ReportVersion",
        on_delete=models.CASCADE,
        related_name="live_for_report",
        null=True,
    )
    draft = models.OneToOneField(
        "ReportVersion",
        on_delete=models.CASCADE,
        related_name="draft_for_report",
        null=True,
    )

    objects = ReportQueryset.as_manager()

    wagtail_reference_index_ignore = True

    class Meta:
        ordering = ("-end_date",)

    def get_absolute_url(self):
        return reverse("apply:projects:reports:detail", kwargs={"pk": self.pk})

    @property
    def previous(self):
        return (
            Report.objects.submitted()
            .filter(
                project=self.project_id,
                end_date__lt=self.end_date,
            )
            .exclude(
                pk=self.pk,
            )
            .first()
        )

    @property
    def next(self):
        return (
            Report.objects.submitted()
            .filter(
                project=self.project_id,
                end_date__gt=self.end_date,
            )
            .exclude(
                pk=self.pk,
            )
            .order_by("end_date")
            .first()
        )

    @property
    def past_due(self):
        return timezone.now().date() > self.end_date

    @property
    def is_very_late(self):
        two_weeks_ago = timezone.now().date() - relativedelta(weeks=2)
        two_weeks_late = self.end_date < two_weeks_ago
        not_submitted = not self.current
        return not_submitted and two_weeks_late

    @property
    def can_submit(self):
        return self.start_date <= timezone.now().date() and not self.skipped

    @property
    def submitted_date(self):
        if self.submitted:
            return self.submitted.date()

    @cached_property
    def start_date(self):
        last_report = self.project.reports.filter(end_date__lt=self.end_date).first()
        if last_report:
            return last_report.end_date + relativedelta(days=1)

        return self.project.start_date


class ReportVersion(BaseStreamForm, AccessFormData, models.Model):
    report = models.ForeignKey(
        "Report", on_delete=models.CASCADE, related_name="versions"
    )
    submitted = models.DateTimeField()
    form_data = models.JSONField(encoder=StreamFieldDataEncoder, default=dict)
    draft = models.BooleanField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reports",
        null=True,
    )

    wagtail_reference_index_ignore = True

    @property
    def form_fields(self):
        return self.report.form_fields


class ReportPrivateFiles(models.Model):
    report = models.ForeignKey(
        "ReportVersion", on_delete=models.CASCADE, related_name="files"
    )
    document = models.FileField(upload_to=report_path, storage=PrivateStorage())

    wagtail_reference_index_ignore = True

    @property
    def filename(self):
        return os.path.basename(self.document.name)

    def __str__(self):
        return self.filename

    def get_absolute_url(self):
        return reverse(
            "apply:projects:reports:document",
            kwargs={"pk": self.report.report_id, "file_pk": self.pk},
        )


class ReportConfig(models.Model):
    """Persists configuration about the reporting schedule etc"""

    WEEK = _("week")
    MONTH = _("month")
    YEAR = _("year")
    FREQUENCY_CHOICES = [
        (WEEK, _("Weeks")),
        (MONTH, _("Months")),
        (YEAR, _("Years")),
    ]

    project = models.OneToOneField(
        "Project", on_delete=models.CASCADE, related_name="report_config"
    )
    schedule_start = models.DateField(null=True)
    occurrence = models.PositiveSmallIntegerField(default=1)
    frequency = models.CharField(choices=FREQUENCY_CHOICES, default=MONTH, max_length=6)
    disable_reporting = models.BooleanField(default=False)
    does_not_repeat = models.BooleanField(default=False)

    def get_frequency_display(self):
        if self.disable_reporting:
            return _("Reporting Disabled")
        if self.does_not_repeat:
            last_report = self.last_report()
            if last_report:
                return _(
                    "One time, that already has reported on {date}".format(
                        date=last_report.end_date.strftime("%d %B, %Y")
                    )
                )
            return _(
                "One time on {date}".format(
                    date=self.schedule_start.strftime("%d %B, %Y")
                )
            )
        next_report = self.current_due_report()

        if self.frequency == self.YEAR:
            if self.schedule_start and self.schedule_start.day == 31:
                day_of_month = _("last day")
                month = self.schedule_start.strftime("%B")
            else:
                day_of_month = ordinal(next_report.end_date.day)
                month = next_report.end_date.strftime("%B")
            if self.occurrence == 1:
                return _("Once a year on {month} {day}").format(
                    day=day_of_month, month=month
                )
            return _("Every {occurrence} years on {month} {day}").format(
                occurrence=self.occurrence, day=day_of_month, month=month
            )

        if self.frequency == self.MONTH:
            if self.schedule_start and self.schedule_start.day == 31:
                day_of_month = _("last day")
            else:
                day_of_month = ordinal(next_report.end_date.day)
            if self.occurrence == 1:
                return _("Once a month on the {day}").format(day=day_of_month)
            return _("Every {occurrence} months on the {day}").format(
                occurrence=self.occurrence, day=day_of_month
            )

        weekday = next_report.end_date.strftime("%A")

        if self.occurrence == 1:
            return _("Once a week on {weekday}").format(weekday=weekday)
        return _("Every {occurrence} weeks on {weekday}").format(
            occurrence=self.occurrence, weekday=weekday
        )

    def is_up_to_date(self):
        return len(self.project.reports.to_do()) == 0

    def outstanding_reports(self):
        return len(self.project.reports.to_do())

    def has_very_late_reports(self):
        return self.project.reports.any_very_late()

    def past_due_reports(self):
        return self.project.reports.to_do()

    def last_report(self):
        today = timezone.now().date()
        # Get the most recent report that was either:
        # - due by today and not submitted
        # - was skipped but due after today
        # - was submitted but due after today
        return self.project.reports.filter(
            Q(end_date__lt=today) | Q(skipped=True) | Q(submitted__isnull=False)
        ).first()

    def current_due_report(self):
        if self.disable_reporting:
            return None

        # Project not started - no reporting required
        if not self.project.start_date:
            return None

        today = timezone.now().date()

        last_report = self.last_report()

        schedule_date = self.schedule_start or self.project.start_date

        if last_report:
            # Frequency is one time and last report exists - no reporting required anymore
            if self.does_not_repeat:
                return None

            if last_report.end_date < schedule_date:
                # reporting schedule changed schedule_start is now the next report date
                next_due_date = schedule_date
            else:
                # we've had a report since the schedule date so base next deadline from the report
                next_due_date = self.next_date(last_report.end_date)
        else:
            # first report required
            if self.schedule_start and self.schedule_start >= today:
                # Schedule changed since project inception
                next_due_date = self.schedule_start
            else:
                # schedule_start is the first day the project so the "last" period
                # ended one day before that. If date is in past we required report now
                if self.does_not_repeat:
                    next_due_date = today
                else:
                    next_due_date = max(
                        self.next_date(schedule_date - relativedelta(days=1)),
                        today,
                    )

        report, _ = self.project.reports.update_or_create(
            project=self.project,
            current__isnull=True,
            skipped=False,
            end_date__gte=today,
            defaults={"end_date": next_due_date},
        )
        return report

    def current_report(self):
        """This is different from current_due_report as it will return a completed report
        if that one is the current one."""
        today = timezone.now().date()

        last_report = self.last_report()

        if last_report and last_report.end_date >= today:
            return last_report

        return self.current_due_report()

    def next_date(self, last_date):
        delta_frequency = self.frequency + "s"
        delta = relativedelta(**{delta_frequency: self.occurrence})
        next_date = last_date + delta
        return next_date
