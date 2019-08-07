from django.conf import settings
from django.db import models
from django.urls import reverse


class Project(models.Model):
    lead = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    submission = models.OneToOneField("funds.ApplicationSubmission", on_delete=models.CASCADE)

    name = models.TextField()

    contact_legal_name = models.TextField(default='')
    contact_email = models.TextField(default='')
    contact_address = models.TextField(default='')
    value = models.DecimalField(default=0, max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

    @classmethod
    def create_from_submission(cls, submission):
        """
        Create a Project from the given submission.

        Returns a new Project or the given ApplicationSubmissions existing
        Project.
        """
        # OneToOne relations on the targetted model cannot be accessed without
        # an exception when the relation doesn't exist (is None).  Since we
        # want to fail fast here, we can use hasattr instead.
        if hasattr(submission, 'project'):
            return submission.project

        return Project.objects.create(
            submission=submission,
            name=submission.title,
            contact_email=submission.user.email,
            contact_legal_name=submission.user.full_name,
            contact_address=submission.form_data.get('address', ''),
            value=submission.form_data.get('value', 0),
        )

    def get_absolute_url(self):
        return reverse('apply:projects:detail', args=[self.id])
