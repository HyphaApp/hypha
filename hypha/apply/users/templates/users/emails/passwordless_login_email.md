{% load i18n wagtailadmin_tags %}{% base_url_setting as base_url %}{% firstof name username as user %}
{% blocktrans %}Dear {{ user }},{% endblocktrans %}

{% if is_active %}
{% blocktrans %}Login to your account on the {{ ORG_LONG_NAME }} web site by clicking this link or copying and pasting it to your browser:{% endblocktrans %}

{% if site %}{{ site.root_url }}{% else %}{{ base_url }}{% endif %}{{ login_path }}

{% blocktrans %}This link will valid for {{ timeout_minutes }} minutes and can be used only once.{% endblocktrans %}

{% else %}
{% blocktrans %}Your account on the {{ ORG_LONG_NAME }} web site is deactivated. Please contact site administrators.{% endblocktrans %}
{% endif %}

{% blocktrans %}If you did not request this email, please ignore it.{% endblocktrans %}

{% if ORG_EMAIL %}
{% blocktrans %}If you have any questions, please contact us at {{ ORG_EMAIL }}.{% endblocktrans %}
{% endif %}

{% blocktrans %}Kind Regards,
The {{ ORG_SHORT_NAME }} Team{% endblocktrans %}

--
{{ ORG_LONG_NAME }}
{% if site %}{{ site.root_url }}{% else %}{{ base_url }}{% endif %}
