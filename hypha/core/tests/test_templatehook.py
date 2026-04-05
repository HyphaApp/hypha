"""Tests for core/templatehook.py — TemplateHook and Hook classes."""

from django.test import SimpleTestCase

from hypha.core.templatehook import Hook, TemplateHook


class TestTemplateHook(SimpleTestCase):
    def setUp(self):
        self.hook = TemplateHook()

    def test_call_with_no_callbacks_returns_empty_list(self):
        self.assertEqual(self.hook(), [])

    def test_register_and_call_callback(self):
        self.hook.register(lambda: "hello")
        result = self.hook()
        self.assertEqual(result, ["hello"])

    def test_multiple_callbacks_all_called(self):
        self.hook.register(lambda: "a")
        self.hook.register(lambda: "b")
        self.assertEqual(self.hook(), ["a", "b"])

    def test_callbacks_receive_arguments(self):
        self.hook.register(lambda x: x * 2)
        self.assertEqual(self.hook(3), [6])

    def test_unregister_removes_callback(self):
        cb = lambda: "x"  # noqa: E731
        self.hook.register(cb)
        self.hook.unregister(cb)
        self.assertEqual(self.hook(), [])

    def test_unregister_nonexistent_callback_is_safe(self):
        # Should not raise
        self.hook.unregister(lambda: "ghost")

    def test_unregister_all_clears_registry(self):
        self.hook.register(lambda: "a")
        self.hook.register(lambda: "b")
        self.hook.unregister_all()
        self.assertEqual(self.hook(), [])

    def test_register_non_callable_raises(self):
        with self.assertRaises(AssertionError):
            self.hook.register("not_callable")

    def test_providing_args_stored(self):
        hook = TemplateHook(providing_args=["foo", "bar"])
        self.assertEqual(hook.providing_args, ["foo", "bar"])


class TestHook(SimpleTestCase):
    def setUp(self):
        self.hook = Hook()

    def test_call_unknown_hook_returns_empty_list(self):
        self.assertEqual(self.hook("missing"), [])

    def test_register_and_call_hook_by_name(self):
        self.hook.register("greet", lambda: "hi")
        self.assertEqual(self.hook("greet"), ["hi"])

    def test_two_hooks_independent(self):
        self.hook.register("a", lambda: 1)
        self.hook.register("b", lambda: 2)
        self.assertEqual(self.hook("a"), [1])
        self.assertEqual(self.hook("b"), [2])

    def test_unregister_removes_specific_callback(self):
        cb = lambda: "x"  # noqa: E731
        self.hook.register("myapp.hook", cb)
        self.hook.unregister("myapp.hook", cb)
        self.assertEqual(self.hook("myapp.hook"), [])

    def test_unregister_nonexistent_hook_is_safe(self):
        self.hook.unregister("ghost", lambda: None)

    def test_unregister_all_clears_named_hook(self):
        self.hook.register("h", lambda: 1)
        self.hook.register("h", lambda: 2)
        self.hook.unregister_all("h")
        self.assertEqual(self.hook("h"), [])

    def test_unregister_all_nonexistent_hook_is_safe(self):
        self.hook.unregister_all("ghost")

    def test_hook_passes_args_to_callbacks(self):
        self.hook.register("double", lambda x: x * 2)
        self.assertEqual(self.hook("double", 5), [10])
