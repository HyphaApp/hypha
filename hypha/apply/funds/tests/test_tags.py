from django.template import Context, Template
from django.test import TestCase

from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory


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
