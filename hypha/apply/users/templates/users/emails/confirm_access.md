{% load i18n wagtailadmin_tags %}{% base_url_setting as base_url %}
{% blocktrans %}Dear {{ user }},{% endblocktrans %}

{% blocktrans %}To confirm access at {{ org_long_name }} use the code below (valid for {{ timeout_minutes }} minutes):{% endblocktrans %}

{{ token }}

{% blocktrans %}If you did not request this email, please ignore it.{% endblocktrans %}

{% if org_email %}
{% blocktrans %}If you have any questions, please contact us at {{ org_email }}.{% endblocktrans %}
{% endif %}

{% blocktrans %}Kind Regards,
The {{ org_short_name }} Team{% endblocktrans %}

--
{{ org_long_name }}
{% if site %}{{ site.root_url }}{% else %}{{ base_url }}{% endif %}
