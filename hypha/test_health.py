from unittest.mock import patch

from django.db import OperationalError
from django.test import TestCase
from django.urls import reverse


class TestHealthCheck(TestCase):
    def test_returns_200_when_db_healthy(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)

    def test_response_body_is_ok_when_healthy(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.content, b"ok")

    def test_content_type_is_text_plain_when_healthy(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response["Content-Type"], "text/plain")

    def test_accessible_without_authentication(self):
        # Health check must be reachable by load balancers without credentials.
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)

    def test_returns_500_when_db_unavailable(self):
        with patch(
            "hypha.health.connection.ensure_connection",
            side_effect=OperationalError("connection refused"),
        ):
            response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 500)

    def test_response_body_is_failed_when_db_unavailable(self):
        with patch(
            "hypha.health.connection.ensure_connection",
            side_effect=OperationalError("connection refused"),
        ):
            response = self.client.get(reverse("health"))
        self.assertEqual(response.content, b"failed")

    def test_content_type_is_text_plain_on_failure(self):
        with patch(
            "hypha.health.connection.ensure_connection",
            side_effect=OperationalError("connection refused"),
        ):
            response = self.client.get(reverse("health"))
        self.assertEqual(response["Content-Type"], "text/plain")

    def test_exception_detail_not_exposed_in_response(self):
        # Internal DB details (host, credentials) must never reach the client.
        with patch(
            "hypha.health.connection.ensure_connection",
            side_effect=OperationalError("secret-db-host:5432 password=hunter2"),
        ):
            response = self.client.get(reverse("health"))
        self.assertNotIn(b"secret-db-host", response.content)
        self.assertNotIn(b"hunter2", response.content)

    def test_logs_error_on_db_failure(self):
        with patch("hypha.health.logger.exception") as mock_log:
            with patch(
                "hypha.health.connection.ensure_connection",
                side_effect=OperationalError("connection refused"),
            ):
                self.client.get(reverse("health"))
        mock_log.assert_called_once()
