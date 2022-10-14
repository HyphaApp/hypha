{% extends "messages/email/base.html" %}
{% load humanize i18n %}

{% block salutation %}### {% trans "Activities Summary" %}{% endblock %}

{% block content %}
{% blocktranslate with total_count_apnumber=total_count|apnumber count counter=total_count %}
There is {{ total_count_apnumber }} new activity:
{% plural %}
There are {{ total_count_apnumber }} new activities:
{% endblocktranslate %}

{% if submissions %}**{% trans "Submissions" %}**
{% for msg in submissions %}
- {{ msg.content_markdown }} • {{ msg.event.when }}{% endfor %}{% endif %}

{% if comments %}**{% trans "Comments" %}**
{% for msg in comments %}
- {{ msg.content_markdown }} • {{ msg.event.when }}{% endfor %}{% endif %}

{% if reviews %}**{% trans "Reviews" %}**
{% for msg in reviews %}
- {{ msg.content_markdown }} • {{ msg.event.when }}{% endfor %}{% endif %}

{% if has_main_sections and messages %}**{% trans "Other activities" %}**{% endif %}
{% for msg in messages %}
- {{ msg.content_markdown }} • {{ msg.event.when }}{% endfor %}
{% endblock content %}
