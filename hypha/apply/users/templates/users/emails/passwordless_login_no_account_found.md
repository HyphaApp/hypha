{% load i18n wagtailadmin_tags %}{% base_url_setting as base_url %}

{% blocktrans %}Dear,{% endblocktrans %}

{% blocktrans %}It looks like you are trying to login on {{ org_long_name }} web site, but we could not find any account with the email provided.{% endblocktrans %}

{% if org_email %}
{% blocktrans %}If you have any questions, please contact us at {{ org_email }}.{% endblocktrans %}
{% endif %}

{% blocktrans %}Kind Regards,
The {{ org_short_name }} Team{% endblocktrans %}

--
{{ org_long_name }}
{% if site %}{{ site.root_url }}{% else %}{{ base_url }}{% endif %}
