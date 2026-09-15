{% load i18n util_tags %}
{% blocktrans %}Dear {{ user }},{% endblocktrans %}

{% blocktrans %}To confirm access at {{ ORG_LONG_NAME }} use the code below (valid for {{ timeout_minutes }} minutes):{% endblocktrans %}

{{ token }}

{% blocktrans %}If you did not request this email, please ignore it.{% endblocktrans %}

{% if ORG_EMAIL %}
{% blocktrans %}If you have any questions, please contact us at {{ ORG_EMAIL }}.{% endblocktrans %}
{% endif %}

{% blocktrans %}Kind Regards,
The {{ ORG_SHORT_NAME }} Team{% endblocktrans %}

--
{{ ORG_LONG_NAME }}
{% base_url %}
