import json
from urllib.parse import urlparse

from django.contrib.messages import get_messages
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin


class HtmxMessageMiddleware(MiddlewareMixin):
    """
    Middleware that transfers Django messages into the HX-Trigger header for HTMX requests.

    This middleware captures Django messages and adds them to the HX-Trigger header
    when the request is made with HTMX. It preserves any existing HX-Trigger values
    and adds the messages in a standardized format that can be processed by frontend
    JavaScript.

    The messages are formatted as an array of objects, each containing:
    - message: The text content of the message
    - tags: CSS class names or other categorization for the message
    """

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        # The HX-Request header indicates that the request was made with HTMX
        if "HX-Request" not in request.headers:
            return response

        # Ignore redirection because HTMX cannot read the headers
        if 300 <= response.status_code < 400:
            return response

        if response.headers.get("HX-Refresh", False):
            return response

        # Extract the messages
        messages = [
            {"message": message.message, "tags": message.tags}
            for message in get_messages(request)
        ]
        if not messages:
            return response

        # Get the existing HX-Trigger that could have been defined by the view
        hx_trigger = response.headers.get("HX-Trigger")

        if hx_trigger is None:
            # If the HX-Trigger is not set, start with an empty object
            hx_trigger = {}
        elif hx_trigger.startswith("{"):
            # If the HX-Trigger uses the object syntax, parse the object
            hx_trigger = json.loads(hx_trigger)
        else:
            # If the HX-Trigger uses the string syntax, convert to the object syntax
            hx_trigger = {hx_trigger: True}

        # Add the messages array in the HX-Trigger object
        hx_trigger["messages"] = messages

        # Add or update the HX-Trigger
        response.headers["HX-Trigger"] = json.dumps(hx_trigger)

        return response


class HtmxAuthRedirectMiddleware:
    """
    Middleware to handle HTMX authentication redirects properly.

    When an HTMX request results in a 302 redirect (typically for authentication),
    this middleware:
    1. Changes the response status code to 204 (No Content)
    2. Adds an HX-Redirect header with the redirect URL
    3. Preserves the original request path in the 'next' query parameter

    This ensures that after authentication, the user is returned to the page
    they were attempting to access, maintaining a seamless UX with HTMX.

    Credits: https://www.caktusgroup.com/blog/2022/11/11/how-handle-django-login-redirects-htmx/
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # HTMX request returning 302 likely is login required.
        # Take the redirect location and send it as the HX-Redirect header value,
        # with 'next' query param set to where the request originated. Also change
        # response status code to 204 (no content) so that htmx will obey the
        # HX-Redirect header value.
        if request.headers.get("HX-Request") == "true" and response.status_code == 302:
            # Determine the next path from referer or current request path
            ref_header = request.headers.get("Referer", "")
            if ref_header:
                referer = urlparse(ref_header)
                next_path = referer.path
            else:
                next_path = request.path

            # Parse the redirect URL
            redirect_url = urlparse(response["location"])

            # Set response status code to 204 for HTMX to process the redirect
            response.status_code = 204

            # Create the redirect URL manually to avoid encoding issues
            if redirect_url.query:
                # Extract the query parameters
                if "next=" in redirect_url.query:
                    # Replace the existing next parameter
                    import re

                    new_query = re.sub(
                        r"next=[^&]*", f"next={next_path}", redirect_url.query
                    )
                else:
                    # Append a new next parameter
                    new_query = f"{redirect_url.query}&next={next_path}"
            else:
                # No existing query parameters
                new_query = f"next={next_path}"

            # Set the new HX-Redirect header
            response.headers["HX-Redirect"] = f"{redirect_url.path}?{new_query}"

        return response
