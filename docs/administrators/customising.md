# Customising

## Templates

You can override any Hypha template by adding a copy inside the `templates_custom` directory.

As an example lets override the `hypha/apply/dashboard/templates/dashboard/applicant_dashboard.html` template.

Place a copy of the template in `hypha/templates_custom/dashboard/applicant_dashboard.html`. Make any needed changes to the template and it will be used instead of the original template.

## Classes

A number of classes can be overridden by settings. You develop your own version of the class in question and then point the setting to that class. It will then be used in place of the default class.

List of classes and their settings:

* aaa -> AAA
* bbb -> BBB