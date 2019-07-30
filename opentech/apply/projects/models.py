from django.db import models
from django.urls import reverse


class Project(models.Model):
    submission = models.OneToOneField("funds.ApplicationSubmission", on_delete=models.CASCADE)

    name = models.TextField()

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
        )

    def get_absolute_url(self):
        return reverse('apply:projects:detail', args=[self.id])
