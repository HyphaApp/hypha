from django.template import Context, Template
from django.test import RequestFactory, TestCase, override_settings

from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory
from hypha.apply.users.tests.factories import ApplicantFactory, StaffFactory


class TestTemplateTags(TestCase):
    def test_markdown_tags(self):
        template = Template("{% load markdown_tags %}{{ content|markdown|safe }}")
        context = Context({"content": "Lorem ipsum **dolor** sit amet."})
        output = template.render(context)
        self.assertEqual(
            output, "<p>Lorem ipsum <strong>dolor</strong> sit amet.</p>\n"
        )

    def test_submission_tags(self):
        submission = ApplicationSubmissionFactory()
        template = Template(
            "{% load submission_tags %}{{ content|submission_links|safe }}"
        )
        context = Context(
            {"content": f"Lorem ipsum dolor #{submission.public_id} sit amet."}
        )
        output = template.render(context)
        assert (
            output
            == f'Lorem ipsum dolor <a href="{submission.get_absolute_url()}">{submission.title} <span class="text-gray-400">#{submission.public_id or submission.id}</span></a> sit amet.'
        )

    @override_settings(APPLICATION_TRANSLATIONS_ENABLED=True)
    def test_translate_tags_as_applicant(self):
        submission = ApplicationSubmissionFactory()
        request = RequestFactory().get(submission.get_absolute_url())
        request.user = ApplicantFactory()
        template = Template(
            "{% load translate_tags %}{% if request.user|can_translate_submission %}<p>some translation stuff</p>{% endif %}"
        )
        context = Context({"request": request})
        output = template.render(context)

        self.assertEqual(output, "")

    @override_settings(APPLICATION_TRANSLATIONS_ENABLED=True)
    def test_translate_tags_as_staff(self):
        submission = ApplicationSubmissionFactory()
        request = RequestFactory().get(submission.get_absolute_url())
        request.user = StaffFactory()
        template = Template(
            "{% load translate_tags %}{% if request.user|can_translate_submission %}<p>some translation stuff</p>{% endif %}"
        )
        context = Context({"request": request})
        output = template.render(context)

        self.assertEqual(output, "<p>some translation stuff</p>")

    @override_settings(APPLICATION_TRANSLATIONS_ENABLED=False)
    def test_translate_tags_disabled(self):
        submission = ApplicationSubmissionFactory()
        request = RequestFactory().get(submission.get_absolute_url())
        request.user = StaffFactory()
        template = Template(
            "{% load translate_tags %}{% if request.user|can_translate_submission %}<p>some translation stuff</p>{% endif %}"
        )
        context = Context({"request": request})
        output = template.render(context)

        self.assertEqual(output, "")
