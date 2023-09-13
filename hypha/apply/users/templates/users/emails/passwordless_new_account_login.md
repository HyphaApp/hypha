{% load i18n wagtailadmin_tags %}{% base_url_setting as base_url %}
{% blocktrans %}Dear,{% endblocktrans %}

{% blocktrans %}Welcome to {{ org_long_name }} web site. Login to your account by clicking this link or copying and pasting it to your browser:{% endblocktrans %}

{% if site %}{{ site.root_url }}{% else %}{{ base_url }}{% endif %}{{ signup_path }}

{% blocktrans %}This link will valid for {{ timeout_hours }} hours and can be used only once.{% endblocktrans %}

{% blocktrans %}If you did not request this email, please ignore it.{% endblocktrans %}

{% if org_email %}
{% blocktrans %}If you have any questions, please contact us at {{ org_email }}.{% endblocktrans %}
{% endif %}

{% blocktrans %}Kind Regards,
The {{ org_short_name }} Team{% endblocktrans %}

--
{{ org_long_name }}
{% if site %}{{ site.root_url }}{% else %}{{ base_url }}{% endif %}
