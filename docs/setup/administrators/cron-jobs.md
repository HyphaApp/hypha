# Possible Cron Commands

Hypha comes stock with management commands that can be utilized in tandem with a job scheduler to automate specific tasks

## Account Cleanup

Accounts that haven't been logged into in 5 months can be marked as inactive with the following command:

```shell
python3 manage.py accounts_cleanup
```

## Drafts Cleanup

Drafts that haven't been modified in a specified time (in days) can be deleted with the following command:

```shell
python3 manage.py drafts_cleanup [days]

# Or, to run without a confirmation prompt

python3 manage.py drafts_cleanup [days] --noinput
```

Example: to delete all drafts that haven't been modified in a year without a confirmation prompt:

```shell
python3 manage.py drafts_cleanup 365 --noinput
```