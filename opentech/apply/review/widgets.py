from django.forms.widgets import Select


class ButtonsAsSelectWidget(Select):
    template_name = 'review/widgets/buttons_select.html'
