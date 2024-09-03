
Notifications are sent through batch channels that use various adapters for each communication channel. 
Each adapter is defined in its own module via a class definition that inherits from base class `AdapterBase`. 
Currently the communication channels we support are email (default), Slackbot, and in-app notifications. On the admin interface, messages can be scheduled and the adapter can be reconfigured.

The types of messages are as follows:

- `SUCCESS`
- `ERROR`
- `WARNING`
- `INFO`

The options for statuses for messages are as follows:

- `APPROVED_BY_FINANCE`
- `APPROVED_BY_STAFF`
- `CHANGES_REQUESTED_BY_FINANCE`
- `CONVERTED`
- `PAID`
- `RESUBMITTED`
- `SUBMITTED`

Messages are rendered using a template defined in `hypha/apply/activity/templates/messages`.

## Notifications and reminders for invoicing and contracting 

These notifications exist to update users on their invoice status and transitions throughout the web app, notifying them if they are required to do anything. 

The default method for notifications are via the email address provided. The communication style is to provide the minimum level of detail in the email and make it required to log in to read the full message. 

Invoice states and who needs to be notified: (states 1-17)
1
…
17 

[add diagram]


## Translation / localization files for automated messages 

`wagtail-localize` is a translation plug-in for the Wagtail CMS, allowing pages or snippets to be translated within Wagtail’s admin interface. Localization happens in `hypha/hypha/apply/funds/templates/funds/tables/table.html` and `hypha/hypha/public/partner/templates/partner/table.html` if a column has a `localize` property. 

For translation, we are using `django.utils` translation library. For this, it is required to set up hooks called translation strings that signify to Django that certain text snippets that are marked should be translated into the end user’s language if possible. 

Messages are translated when the email is constructed in `make_email_object` in `hypha/hypha/core/mail.py` 

```python
def make_email_object(self, to: str | List[str], context, **kwargs):
    if not isinstance(to, (list, tuple)):
        to = [to]

    lang = context.get('lang', None) or settings.LANGUAGE_CODE

    with language(lang):
        rendered_template = self._render_template(context)
        body_txt = cleanup_markdown(rendered_template)
        body_html = markdown_to_html(rendered_template)

    email = EmailMultiAlternatives(**kwargs)
    email.body = body_txt
    email.attach_alternative(body_html, 'text/html')

    email.to = to

    return email
```
