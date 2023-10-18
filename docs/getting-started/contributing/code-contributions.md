# Code Contributions

## Creating Pull Requests

Found a bug and know how to fix it? Have some design wireframes to improve some usability issues? Translated Hypha into another language? Built a new feature you want to add? Please submit an issue or create a pull request on [GitHub](https://github.com/HyphaApp/hypha/issues).

Guidance for contributing code:

1. [Submitting Changes](submitting-changes.md)
2. [Hypha Architecture](../../getting-started/architecture.md)


## Testing

### Test Class Helpers

[BaseViewTestCase](https://github.com/HyphaApp/hypha/blob/main/hypha/apply/utils/testing/tests.py) provides a useful framework for testing views. It handles the setup of requests and simplifies common url operations for views in the same installed app.

### Reversing URLS

Due to the way the urls are [configured](https://github.com/HyphaApp/meta/tree/6060bb2491e501e501979a68036dd52f60f6a6fe/Contributing/Implementation.md#url-configuration), tests for the Apply site will fail as the Apply site does not use the default URL config.

This can be resolved on a per testcase basis using the following:

```python
from django.test import TestCase, override_settings

@override_settings(ROOT_URLCONF='hypha.apply.urls')
class MyTestCase(TestCase):
  pass
```

This is implemented by default for the [BaseViewTestCase](testing.md#test-class-helpers)

