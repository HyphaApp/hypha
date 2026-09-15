{% load i18n util_tags %}
{% blocktrans %}Dear {{ user }},{% endblocktrans %}

{% blocktrans %}This is to notify you that your account was successfully logged in to {{ ORG_LONG_NAME }}.{% endblocktrans %}

{% blocktrans with login_time=login_time %}Login time: {{ login_time }}{% endblocktrans %}

{% blocktrans %}If you did not log in, please contact us immediately and consider changing your password.{% endblocktrans %}

{% if ORG_EMAIL %}
{% blocktrans %}If you have any questions, please contact us at {{ ORG_EMAIL }}.{% endblocktrans %}
{% endif %}

{% blocktrans %}Kind Regards,
The {{ ORG_SHORT_NAME }} Team{% endblocktrans %}

--
{{ ORG_LONG_NAME }}
{% base_url %}
