import pytest

from hypha.core.utils import markdown_to_html

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


@pytest.mark.parametrize('test_input,expected', markdown_test_dataset)
def test_markdown_to_html(test_input, expected):
    output = markdown_to_html(test_input).replace('\n', '').replace('  ', '')
    assert output == expected
