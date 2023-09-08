# Path: hypha/apply/search/tests/test_query_parser.py

import pytest

from ..query_parser import parse_search_query, tokenize_date_filter_value


@pytest.mark.parametrize(
    "query, expected",
    [
        ("", {"filters": {}, "text": ""}),
        ("#12 #13", {"filters": {"id": [12, 13]}, "text": ""}),
        ("text before #12", {"filters": {"id": [12]}, "text": "text before"}),
        ("#12 text after", {"filters": {"id": [12]}, "text": "text after"}),
        ("hello", {"filters": {}, "text": "hello"}),
        (
            "submitted:2023-12-02 hello",
            {"filters": {"submitted": ["2023-12-02"]}, "text": "hello"},
        ),
        (
            "submitted:>2023-12-02 submitted:<2023-12-01 hello",
            {"filters": {"submitted": [">2023-12-02", "<2023-12-01"]}, "text": "hello"},
        ),
        (
            'submitted:"hello world"',
            {"filters": {"submitted": ["hello world"]}, "text": ""},
        ),
        ('"hello world"', {"filters": {}, "text": '"hello world"'}),
    ],
)
def test_parse_search_query(query, expected):
    assert parse_search_query(query) == expected


@pytest.mark.parametrize(
    "date_str, expected",
    [
        (">2023-12-02", [">", 2023, 12, 2]),
        ("<2023-12-01", ["<", 2023, 12, 1]),
        ("<=2023-12-01", ["<=", 2023, 12, 1]),
        (">=2023-12-01", [">=", 2023, 12, 1]),
        (">=2023-12", [">=", 2023, 12]),
        ("2023-12", [None, 2023, 12]),
        ("2023-24", []),
        ("1111-12-89", []),
        ("2023", [None, 2023]),
        (">2023", [">", 2023]),
    ],
)
def test_tokenize_date_filter_value(date_str, expected):
    assert tokenize_date_filter_value(date_str=date_str) == expected
