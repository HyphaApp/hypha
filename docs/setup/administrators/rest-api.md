# RESTful APIs

For documentation on existing REST APIs, see the [REST API reference page](../../references/rest-api.md)

## Setting Up & Utilizing API Keys

Hypha's REST APIs are built utilizing the [django-rest-framework](https://www.django-rest-framework.org).

APIs require an API Key to be used, which can be generated the Django Admin Console. For more information on creation/management, see the [djangorestframework-api-key documentation](https://florimondmanca.github.io/djangorestframework-api-key/guide/#creating-and-managing-api-keys)

Unless the default settings are changed, `Authorization: Api-Key <API_KEY>` will be expected as an HTTP header in all API requests, with `<API_KEY>` being replaced with the generated key.