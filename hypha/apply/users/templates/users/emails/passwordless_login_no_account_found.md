{% load i18n wagtailadmin_tags %}{% base_url_setting as base_url %}

{% blocktrans %}Dear,{% endblocktrans %}

{% blocktrans %}It looks like you are trying to login on {{ ORG_LONG_NAME }} web site, but we could not find any account with the email provided.{% endblocktrans %}

{% if ORG_EMAIL %}
{% blocktrans %}If you have any questions, please contact us at {{ ORG_EMAIL }}.{% endblocktrans %}
{% endif %}

{% blocktrans %}Kind Regards,
The {{ ORG_SHORT_NAME }} Team{% endblocktrans %}

--
{{ ORG_LONG_NAME }}
{% if site %}{{ site.root_url }}{% else %}{{ base_url }}{% endif %}
