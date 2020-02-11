from django.template import Context, Template
from django.test import override_settings, TestCase

from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory


@override_settings(ROOT_URLCONF='opentech.apply.urls')
class TestTemplateTags(TestCase):
    def test_markdown_tags(self):
        template = Template('{% load markdown_tags %}{{ content|markdown|safe }}')
        context = Context({'content': 'Lorem ipsum **dolor** sit amet.'})
        output = template.render(context)
        self.assertEqual(output, '<p>Lorem ipsum <strong>dolor</strong> sit amet.</p>\n')

    def test_submission_tags(self):
        submission = ApplicationSubmissionFactory()
        template = Template('{% load submission_tags %}{{ content|submission_links|safe }}')
        context = Context({'content': f'Lorem ipsum dolor #{submission.id} sit amet.'})
        output = template.render(context)
        self.assertEqual(output, f'Lorem ipsum dolor <a href="{submission.get_absolute_url()}">{submission.title} <span class="mid-grey-text">#{submission.id}</span></a> sit amet.')
