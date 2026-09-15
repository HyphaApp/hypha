import pytest
from django.test import override_settings
from wagtail.models import Site

from hypha.core.utils import get_base_url, markdown_to_html

markdown_test_dataset = [
    ("**bold**", "<p><strong>bold</strong></p>"),
    ("~~strike~~", "<p><del>strike</del></p>"),
    (
        """Header1 | Header2
------ | ------
Cell1  | Cell2""",
        "<table><thead><tr><th>Header1</th><th>Header2</th>"
        "</tr></thead><tbody><tr><td>Cell1</td><td>Cell2</td></tr></tbody></table>",
    ),
]


@pytest.mark.parametrize("test_input,expected", markdown_test_dataset)
def test_markdown_to_html(test_input, expected):
    output = markdown_to_html(test_input).replace("\n", "").replace("  ", "")
    assert output == expected


@override_settings(WAGTAILADMIN_BASE_URL="https://apply.example.org")
def test_get_base_url_uses_the_setting():
    assert get_base_url() == "https://apply.example.org"


@override_settings(WAGTAILADMIN_BASE_URL="https://apply.example.org/")
def test_get_base_url_strips_trailing_slash():
    assert get_base_url() == "https://apply.example.org"


@pytest.mark.django_db
@override_settings(WAGTAILADMIN_BASE_URL=None)
def test_get_base_url_falls_back_to_the_default_site():
    site = Site.objects.get(is_default_site=True)
    assert get_base_url() == site.root_url
