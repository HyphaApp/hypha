"""Tests for HtmxMessageMiddleware."""

import json

from django.contrib.messages import constants
from django.contrib.messages.storage.cookie import CookieStorage
from django.http import HttpRequest, HttpResponse
from django.test import SimpleTestCase

from hypha.core.middleware.htmx import HtmxMessageMiddleware


def _make_request(htmx=True, messages=None):
    request = HttpRequest()
    request.META["SERVER_NAME"] = "localhost"
    request.META["SERVER_PORT"] = "80"
    if htmx:
        request.META["HTTP_HX_REQUEST"] = "true"
    # Use CookieStorage — doesn't require session middleware
    storage = CookieStorage(request)
    if messages:
        for msg, level in messages:
            storage.add(level, msg)
    request._messages = storage
    return request


class TestHtmxMessageMiddleware(SimpleTestCase):
    def setUp(self):
        self.middleware = HtmxMessageMiddleware(get_response=lambda r: HttpResponse())

    def _process(self, request, response):
        return self.middleware.process_response(request, response)

    def test_non_htmx_request_returned_unchanged(self):
        request = _make_request(htmx=False, messages=[("hello", constants.INFO)])
        response = HttpResponse()
        result = self._process(request, response)
        self.assertNotIn("HX-Trigger", result)

    def test_no_messages_returns_response_unchanged(self):
        request = _make_request(htmx=True)
        response = HttpResponse()
        result = self._process(request, response)
        self.assertNotIn("HX-Trigger", result)

    def test_messages_added_to_hx_trigger(self):
        request = _make_request(htmx=True, messages=[("Test msg", constants.SUCCESS)])
        response = HttpResponse()
        result = self._process(request, response)
        self.assertIn("HX-Trigger", result)
        trigger = json.loads(result["HX-Trigger"])
        self.assertIn("messages", trigger)
        self.assertEqual(trigger["messages"][0]["message"], "Test msg")

    def test_message_tags_included(self):
        request = _make_request(htmx=True, messages=[("err", constants.ERROR)])
        response = HttpResponse()
        result = self._process(request, response)
        trigger = json.loads(result["HX-Trigger"])
        self.assertIn("tags", trigger["messages"][0])

    def test_multiple_messages_all_included(self):
        request = _make_request(
            htmx=True,
            messages=[("msg1", constants.INFO), ("msg2", constants.WARNING)],
        )
        response = HttpResponse()
        result = self._process(request, response)
        trigger = json.loads(result["HX-Trigger"])
        self.assertEqual(len(trigger["messages"]), 2)

    def test_redirect_response_skipped(self):
        request = _make_request(htmx=True, messages=[("hello", constants.INFO)])
        response = HttpResponse(status=302)
        result = self._process(request, response)
        self.assertNotIn("HX-Trigger", result)

    def test_hx_refresh_response_skipped(self):
        request = _make_request(htmx=True, messages=[("hello", constants.INFO)])
        response = HttpResponse()
        response["HX-Refresh"] = "true"
        result = self._process(request, response)
        # HX-Trigger should not be set (middleware exits early)
        self.assertNotIn("HX-Trigger", result)

    def test_existing_hx_trigger_string_merged(self):
        request = _make_request(htmx=True, messages=[("ok", constants.SUCCESS)])
        response = HttpResponse()
        response["HX-Trigger"] = "myEvent"
        result = self._process(request, response)
        trigger = json.loads(result["HX-Trigger"])
        self.assertIn("myEvent", trigger)
        self.assertIn("messages", trigger)

    def test_existing_hx_trigger_object_merged(self):
        request = _make_request(htmx=True, messages=[("ok", constants.SUCCESS)])
        response = HttpResponse()
        response["HX-Trigger"] = json.dumps({"existingEvent": True})
        result = self._process(request, response)
        trigger = json.loads(result["HX-Trigger"])
        self.assertIn("existingEvent", trigger)
        self.assertIn("messages", trigger)
