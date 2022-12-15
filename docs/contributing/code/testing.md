# Testing

## Test Class Helpers

[BaseViewTestCase](https://github.com/HyphaApp/hypha/blob/main/hypha/apply/utils/testing/tests.py) provides a useful framework for testing views. It handles the setup of requests and simplifies common url operations for views in the same installed app.

## Reversing URLS

Due to the way the urls are [configured](https://github.com/HyphaApp/meta/tree/6060bb2491e501e501979a68036dd52f60f6a6fe/Contributing/Implementation.md#url-configuration), tests for the Apply site will fail as the Apply site does not use the default URL config.

This can be resolved on a per testcase basis using the following:

```python
from django.test import TestCase, override_settings

@override_settings(ROOT_URLCONF='hypha.apply.urls')
class MyTestCase(TestCase):
  pass
```

This is implemented by default for the [BaseViewTestCase](testing.md#test-class-helpers)

