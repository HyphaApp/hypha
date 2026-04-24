# Possible cron commands

Hypha comes stock with management commands that can be utilized in tandem with a job scheduler to automate specific tasks

## Account cleanup

Accounts that haven't been logged into in 5 months can be marked as inactive with the following command:

```shell
python3 manage.py accounts_cleanup
```

## Submission cleanup

There are two options for the cleaning up of user submissions
 * Drafts: **deletes** all drafts outside the specified timeframe. Drafts are never anonymized.
 * Submissions: by default, anonymizes all submissions that are not drafts outside the specified timeline.
    * If `--delete` is specified, the submissions will be deleted instead of anonymized.

```shell
python3 manage.py submission_cleanup --drafts [days] --submissions [days]

# Or, to run without a confirmation prompt

python3 manage.py submission_cleanup --drafts [days] --submissions [days] --noinput
```

Example: to delete all drafts that haven't been modified in a year without a confirmation prompt:

```shell
python3 manage.py submission_cleanup --drafts [days] 365 --noinput
```
