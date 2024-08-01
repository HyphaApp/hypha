from django.test import TestCase
from django.test.client import RequestFactory

from hypha.core.templatetags.querystrings import (
    add_to_query,
    construct_query_string,
    modify_query,
    remove_from_query,
)


class QueryParamsTemplateTagTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.factory = RequestFactory()

    @classmethod
    def tearDownClass(cls):
        pass

    def test_construct_query_string(self):
        # Given a request without any special query parameters and a template name
        request = self.factory.get("/en/test/")

        query_params = [
            ["a", "1"],
            ["a", 2],
            ["b", 3],
            ["c", "OK"],
            ["d", "Hello, World!"],
        ]
        path = construct_query_string(
            context={"request": request}, query_params=query_params
        )

        self.assertEqual(
            path, "/en/test/?a=1&amp;a=2&amp;b=3&amp;c=OK&amp;d=Hello%2C+World%21"
        )

    def test_construct_query_string_only_query_string(self):
        # Given a request without any special query parameters and a template name
        request = self.factory.get("/en/test/")

        query_params = [
            ["a", "1"],
            ["a", 2],
            ["b", 3],
            ["c", "OK"],
            ["d", "Hello, World!"],
        ]
        path = construct_query_string(
            context={"request": request},
            query_params=query_params,
            only_query_string=True,
        )

        self.assertEqual(path, "?a=1&amp;a=2&amp;b=3&amp;c=OK&amp;d=Hello%2C+World%21")

    def test_modify_query(self):
        request = self.factory.get("/en/test/?a=1&a=2&b=3&c=OK&d=Hello%2C+World%21")

        params_to_remove = ["c"]
        params_to_change = {"a": 3, "b": 4}

        path = modify_query({"request": request}, *params_to_remove, **params_to_change)

        # Then we should get the template names saved in context variables
        self.assertEqual(path, "/en/test/?a=3&amp;b=4&amp;d=Hello%2C+World%21")

    def test_modify_query_only_query_string(self):
        request = self.factory.get("/en/test/?a=1&a=2&b=3&c=OK&d=Hello%2C+World%21")

        params_to_remove = ["only_query_string", "c"]
        params_to_change = {"a": 3, "b": 4}

        path = modify_query({"request": request}, *params_to_remove, **params_to_change)

        # Then we should get the template names saved in context variables
        self.assertEqual(path, "?a=3&amp;b=4&amp;d=Hello%2C+World%21")

    def test_add_to_query(self):
        request = self.factory.get("/en/test/?a=1&a=2&b=3&c=OK&d=Hello%2C+World%21")

        params_to_remove = ["c"]
        params_to_add = {"a": 3, "b": 4}

        path = add_to_query({"request": request}, *params_to_remove, **params_to_add)

        # Then we should get the template names saved in context variables
        self.assertEqual(
            path,
            "/en/test/?a=1&amp;a=2&amp;a=3&amp;b=3&amp;b=4&amp;d=Hello%2C+World%21",
        )

    def test_add_to_query_only_query_string(self):
        request = self.factory.get("/en/test/?a=1&a=2&b=3&c=OK&d=Hello%2C+World%21")

        params_to_remove = ["only_query_string", "c"]
        params_to_add = {"a": 3, "b": 4}

        path = add_to_query({"request": request}, *params_to_remove, **params_to_add)

        # Then we should get the template names saved in context variables
        self.assertEqual(
            path,
            "?a=1&amp;a=2&amp;a=3&amp;b=3&amp;b=4&amp;d=Hello%2C+World%21",
        )

    def test_remove_from_query(self):
        request = self.factory.get("/en/test/?a=1&a=2&b=3&c=OK&d=Hello%2C+World%21")

        args = ["c"]
        kwargs = {"a": 2}

        path = remove_from_query({"request": request}, *args, **kwargs)

        # Then we should get the template names saved in context variables
        self.assertEqual(path, "/en/test/?a=1&amp;b=3&amp;d=Hello%2C+World%21")

    def test_remove_from_query_only_query_string(self):
        request = self.factory.get("/en/test/?a=1&a=2&b=3&c=OK&d=Hello%2C+World%21")

        args = ["only_query_string", "c"]
        kwargs = {"a": 2}

        path = remove_from_query({"request": request}, *args, **kwargs)

        # Then we should get the template names saved in context variables
        self.assertEqual(path, "?a=1&amp;b=3&amp;d=Hello%2C+World%21")
