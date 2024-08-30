# Setting up notifications in Hypha

As mentioned in [External Integrations](../../getting-started/architecture.md#external-integrations), Hypha offers notifications via e-mail and/or Slack.

## Notification providers setup

Hypha sends messages via configured providers such as email or Slack.

### Email

For information on configuring email notifications for Hypha, see the [E-mail section](configuration.md#e-mail-settings) of the configuration reference.

### Slack

For information on configuring Slack notifications for Hypha, see the [Slack section](configuration.md/#slack-settings) of the configuration reference.

## Project report reminders

To send reminders for upcoming due reports, configure the following three things.

### Wagtail administration project settings for report reminders

Visit Wagtail admin, click Projects -> Project Settings (or URL `/admin/settings/application_projects/projectsettings`).

Scroll down to add "Report reminder frequency" configurations. Click "Add report reminder frequency" for each reminder.

### Script to run `notify_report_due` command

Create a script that runs the `django` manage command `notify_report_due`.

For example,

```shell
#!/bin/bash

APP_ROOT=/opt/hypha
cd "${APP_ROOT}" || exit 1
export DJANGO_SETTINGS_MODULE="hypha.settings.production"

exec venv/hypha/bin/python3 manage.py notify_report_due
```

The example assumes Hypha is installed at `/opt/hypha`, uses a virtual environment `venv/hypha`, with production
settings.  Adjust as needed for your environment and settings. Make sure that the settings has `SEND_MESSAGES = True`.

### Mechanism to run the above script

Create a regularly executing task that runs the above script.

For example,

```cron
37 9 * * * /usr/local/bin/send-report-reminders.sh
```

The example assumes `cron`, that the shell script calling `notify_report_due` is in `/usr/local/bin` and is executable,
and that the report reminders (when needed) should be sent at 9:37 am according to the system clock.
