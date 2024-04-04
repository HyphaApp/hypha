# Filtering and searching application submissions (beta)

## Using search to filter application submissions

You can use advanced filters to search for application submissions that meet specific criteria.

- Filter archived applications submission: `is:archived`. You must have access to archived submissions and have show archived submissions turned on.
- Filter when applications were submitted: `submitted:2023-09-01`, `submitted:>2023-01`, `submitted:<=2023`
- Filter when applications was last updated: `updated:2023-09-01`, `updated:>2023-01`, `updated:<=2023`
- Filter your flagged submissions: `flagged:@me`
- Filter staff flagged submissions: `flagged:@staff`


## Sharing Filters

When you filter or sort issues and pull requests, your browser's URL is automatically updated to match the new view.

You can send the URL that issues generates to any user, and they'll be able to see the same filter view that you see.

For example, if you filter on submissions assigned to a Lead, and sort on the oldest open issues, your URL would update to something like the following:

```
?lead=33&sort=updated-asc
```
