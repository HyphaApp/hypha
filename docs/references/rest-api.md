# RESTful APIs

For documentation on setting up REST APIs, see the [REST API setup page](../setup/administrators/rest-api.md)

## Endpoints

| Verb | Path                                       | Use                                         | Notes |
|------|--------------------------------------------|---------------------------------------------|-------|
| GET  | [`/api/v1/rounds/open`](#open-rounds-labs) | Get a JSON output of all open rounds & labs |       |


## Open Rounds & Labs

```
GET /api/v1/rounds/open
```

Provides a paginated output of all open rounds and labs within Hypha

Example output:

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 10,
      "title": "Old Fashioned Test Lab",
      "url_path": "/apply/test-lab/",
      "search_description": "",
      "start_date": null,
      "end_date": null,
      "description": "",
      "image": null,
      "weight": 1,
      "landing_url": "http://localhost:9001/test-lab/"
    },
    {
      "id": 46,
      "title": "Cool Test Round",
      "url_path": "/apply/fool-fund/cool-round/",
      "search_description": "",
      "start_date": "2024-12-06",
      "end_date": "2025-03-25",
      "description": "This is such a cool test fund! Come apply!",
      "image": null,
      "weight": 1,
      "landing_url": "http://your-hypha-instance-here.com/cool-fund/"
    },
  ]
}
```