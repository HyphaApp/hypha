{% load i18n wagtailadmin_tags %}{% base_url_setting as base_url %}
{% blocktrans %}Dear {{ user }},{% endblocktrans %}

{% blocktrans %}This is to notify you that a passkey was removed from your account at {{ ORG_LONG_NAME }}.{% endblocktrans %}

{% blocktrans %}Passkey: {{ passkey_name }}{% endblocktrans %}
{% blocktrans with event_time=event_time %}Removed: {{ event_time }}{% endblocktrans %}

{% blocktrans %}If you did not remove this passkey, please contact us immediately and consider changing your password if you have one.{% endblocktrans %}

{% if ORG_EMAIL %}
{% blocktrans %}If you have any questions, please contact us at {{ ORG_EMAIL }}.{% endblocktrans %}
{% endif %}

{% blocktrans %}Kind Regards,
The {{ ORG_SHORT_NAME }} Team{% endblocktrans %}

--
{{ ORG_LONG_NAME }}
{% if site %}{{ site.root_url }}{% else %}{{ base_url }}{% endif %}
