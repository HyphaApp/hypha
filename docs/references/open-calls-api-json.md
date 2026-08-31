# Open calls API endpoint

At `/api/v2/open-calls.json` that same lists and order of open calls that appear on the front page are available in JSON format.

```json
[
    {
        "description": "The application description if any.",
        "image": "/path/to/application/image.jpeg",
        "next_deadline": "1970-01-01",
        "title": "Title of the application",
        "weight": 1
    }
]
```

This should make it easy to add a list of open calls to the organisations main web site.
