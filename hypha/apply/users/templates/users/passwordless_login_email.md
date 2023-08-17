{% load i18n wagtailadmin_tags %}{% base_url_setting as base_url %}{% firstof name username as user %}
{% blocktrans %}Dear {{ user }},{% endblocktrans %}

{% blocktrans %}Login to your account on the {{ org_long_name }} web site by clicking this link or copying and pasting it to your browser:{% endblocktrans %}

[{% if site %}{{ site.root_url }}{% else %}{{ base_url }}{% endif %}{{ activation_path }}]({% if site %}{{ site.root_url }}{% else %}{{ base_url }}{% endif %}{{ activation_path }})

{% blocktrans %}This link can be used only once and will lead you to a page where you can set your password. It will remain active for {{ timeout_hours }} hours.{% endblocktrans %}

{% blocktrans %}If you do not complete the login process within {{ timeout_hours }} hours, you can request another login link at {% endblocktrans %}: [{% if site %}{{ site.root_url }}{% else %}{{ base_url }}{% endif %}{% url 'users_public:passwordless_login_signup' %}]({% if site %}{{ site.root_url }}{% else %}{{ base_url }}{% endif %}{% url 'users_public:passwordless_login_signup' %})

{% blocktrans %}Kind Regards,
The {{ org_short_name }} Team{% endblocktrans %}

--
{{ org_long_name }}
{% if site %}{{ site.root_url }}{% else %}{{ base_url }}{% endif %}
