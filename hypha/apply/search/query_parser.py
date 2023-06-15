import datetime as dt
import re

from lark import Lark, Transformer


# Custom transformer to convert parse tree to a dictionary
class QueryTransformer(Transformer):
    def expression(self, items):
        filters = {}
        text = []
        for item in items:
            if isinstance(item, dict):
                for key, value in item.items():
                    if key in filters:
                        filters[key].append(value)
                    else:
                        filters[key] = [value]
            else:
                text.append(item)
        return {"filters": filters, "text": " ".join(str(t) for t in text)}

    def filter_expression(self, items):
        if len(items) == 3:
            key = items[0]
            value = items[2]
            return {key: value}
        else:
            return {"id": items[1]}

    def search_term(self, items):
        return items[0]

    def string(self, s):
        (s,) = s
        return s.value

    def NUMBER(self, s):
        return int(s.value)

    def ESCAPED_STRING(self, s):
        return s.value[1:-1]


# Define the grammar
parser = Lark(
    r'''
    ?start: expression

    expression: (filter_expression | search_term)*
    filter_expression: string FILTER_COLON string
                    | string FILTER_COLON ESCAPED_STRING
                    | FILTER_HASH NUMBER
    search_term: string
    filer_value: string
            | ESCAPED_STRING

    string: /[^:#\s]+/

    FILTER_COLON: ":"
    FILTER_HASH: "#"

    %import common.NUMBER
    %import common.ESCAPED_STRING
    %ignore /\s+/
''',
    start='start',
    parser='lalr',
    transformer=QueryTransformer()
)


def tokenize_date_filter_value(date_str: str) -> list:
    """Convert a date filter string into a list of tokens.

    Format: [operator][year][-[month]-[day]]
    The tokens are:
    - The operator (>=, <=, >, <) (if present)
    - The year
    - The month (if present)
    - The day (if present)
    """
    # Define the regex pattern
    regex_pattern = r"^(<=|>=|<|>)?(\d{4}(?:-\d{2}(?:-\d{2})?)?(?:-\d{2})?)$"

    # Match the regex pattern to the value
    match = re.match(regex_pattern, date_str)

    # Extract the operator and date from the match object
    operator = match.group(1)
    date_str = match.group(2)

    # Convert date_str to a datetime object
    match len(date_str):
        case 4:
            # Date string is only a year
            return [operator, int(date_str)]
        case 7:
            # Date string is in the format YYYY-MM
            try:
                date = dt.datetime.strptime(date_str, "%Y-%m")
                return [operator, date.year, date.month]
            except ValueError:
                return []
        case _:
            try:
                date = dt.datetime.strptime(date_str, "%Y-%m-%d")
                return [operator, date.year, date.month, date.day]
            except ValueError:
                return []


def parse_search_query(search_query: str) -> dict:
    """
    Parses Gmail-like search query string into a dictionary of filters and
    the remaining text.
    Example: "from:johndoe@example.com to:janedoe@example.com subject:hello world #12"
    would be parsed into:
    {
        "filters": {
            "from": ["johndoe@example.com"],
            "to": ["janedoe@example.com"],
            "subject": ["hello", "world"],
            "id": ["12"]
        },
        "text": "hello world"
    }
    """
    return parser.parse(search_query)
