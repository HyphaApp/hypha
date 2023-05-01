import datetime as dt
import re


def tokenize_date_filter_value(date_str: str)-> list:
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
    filter_pattern = r'(\w+):("[^"]+"|\S+)'
    id_pattern = r'#(\d+)'
    filters = {}
    remaining_text = search_query
    for match in re.finditer(filter_pattern, search_query):
        filter_name, filter_value = match.groups()
        # Remove quotes if present
        if filter_value.startswith('"') and filter_value.endswith('"'):
            filter_value = filter_value[1:-1]
        # Append to existing list if filter already exists
        if filter_name.lower() in filters:
            filters[filter_name.lower()].append(filter_value)
        else:
            filters[filter_name.lower()] = [filter_value]
        # Remove filter from remaining text
        remaining_text = remaining_text.replace(match.group(0), '').strip()

    # Add id filter if present
    for match in re.finditer(id_pattern, remaining_text):
        if "id" in filters:
            filters["id"].append(match.group(1))
        else:
            filters['id'] = [match.group(1)]
        remaining_text = remaining_text.replace(match.group(0), '').strip()
    return {"filters": filters, "text": remaining_text}
