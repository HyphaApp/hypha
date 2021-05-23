from unittest import mock

from django.test import SimpleTestCase, override_settings

from hypha.apply.utils.templatetags.webpack_tags import render_bundle


class WebpackTagsTestCase(SimpleTestCase):

    @override_settings(ENABLE_WEBPACK_BUNDLES=True)
    def test_render_bundle_calls_webpack_loader_when_enabled(self):
        render_bundle_path = 'hypha.apply.utils.templatetags.webpack_tags.webpack_loader.render_bundle'

        with mock.patch(render_bundle_path, return_value='foo.js') as mocked_render_bundle:
            self.assertEqual(render_bundle('foo', 'js'), 'foo.js')

            mocked_render_bundle.assert_called_once_with('foo', 'js', 'DEFAULT', '')

    @override_settings(ENABLE_WEBPACK_BUNDLES=False)
    def test_render_bundle_does_not_call_webpack_loader_when_disabled(self):
        render_bundle_path = 'hypha.apply.utils.templatetags.webpack_tags.webpack_loader.render_bundle'

        with mock.patch(render_bundle_path, return_value='foo.js') as mocked_render_bundle:
            self.assertEqual(render_bundle('foo', 'js'), '')

            self.assertFalse(mocked_render_bundle.called)
