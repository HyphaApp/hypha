import pytest
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import path
from django.views.decorators.http import require_GET

from hypha.apply.users.tests.factories import UserFactory
from hypha.core.middleware.htmx import HtmxAuthRedirectMiddleware


# Create test views
@require_GET
def public_view(request):
    return HttpResponse("Public view")


@login_required
@require_GET
def private_view(request):
    return HttpResponse("Private view")


# Create test URL patterns
urlpatterns = [
    path("public/", public_view, name="public"),
    path("private/", private_view, name="private"),
]


# Mock response handler for middleware
def get_auth_redirect_response(request):
    # For authenticated paths, return a redirect response
    if request.path == "/private/":
        response = HttpResponse()
        response.status_code = 302
        response["Location"] = "/accounts/login/?next=/some/path/"
        return response
    # For non-auth paths, return a regular response
    elif request.path == "/public/":
        response = HttpResponse("Public content")
        return response
    # For other redirects
    elif request.path == "/redirect/":
        response = HttpResponse()
        response.status_code = 302
        response["Location"] = "/other-page/"
        return response
    return HttpResponse()


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def middleware():
    return HtmxAuthRedirectMiddleware(get_response=get_auth_redirect_response)


@pytest.fixture
def settings_with_login_url(settings):
    settings.LOGIN_URL = "/accounts/login/"
    return settings


def test_htmx_auth_redirect(request_factory, middleware, settings_with_login_url):
    """Test that HTMX requests to authenticated views are redirected."""
    # Create a request with HTMX headers
    request = request_factory.get("/private/")
    request.headers = {"HX-Request": "true"}
    request.path = "/private/"

    # Process the request through middleware
    response = middleware(request)

    # Check that the response is modified with HX-Redirect
    assert response.status_code == 204
    assert response.headers["HX-Redirect"] == "/accounts/login/?next=%2Fprivate%2F"


def test_htmx_auth_redirect_with_referer(
    request_factory, middleware, settings_with_login_url
):
    """Test that HTMX requests with Referer header are redirected correctly."""
    # Create a request with HTMX headers and Referer
    request = request_factory.get("/private/")
    request.headers = {
        "HX-Request": "true",
        "Referer": "https://example.com/some/page/",
    }
    request.path = "/private/"

    # Process the request through middleware
    response = middleware(request)

    # Check that the response uses the Referer's path in the next parameter
    assert response.status_code == 204
    assert response.headers["HX-Redirect"] == "/accounts/login/?next=%2Fsome%2Fpage%2F"


def test_non_htmx_request_not_redirected(
    request_factory, middleware, settings_with_login_url
):
    """Test that non-HTMX requests are not affected."""
    # Create a regular request without HTMX headers
    request = request_factory.get("/private/")
    request.headers = {}
    request.path = "/private/"

    # Process the request through middleware
    response = middleware(request)

    # Assert that the middleware didn't change the response status
    assert response.status_code == 302
    assert "HX-Redirect" not in response.headers
    assert response["Location"] == "/accounts/login/?next=/some/path/"


def test_htmx_non_auth_redirect_not_affected(
    request_factory, middleware, settings_with_login_url
):
    """Test that HTMX requests with non-auth redirects are not affected."""
    # Create a request with HTMX headers to a path that redirects elsewhere
    request = request_factory.get("/redirect/")
    request.headers = {"HX-Request": "true"}
    request.path = "/redirect/"

    # Process the request through middleware
    response = middleware(request)

    # Assert that the middleware handles the redirect with HX-Redirect
    assert response.status_code == 204
    assert response.headers["HX-Redirect"] == "/other-page/?next=%2Fredirect%2F"


def test_htmx_normal_request(request_factory, middleware, settings_with_login_url):
    """Test that HTMX requests to public views work normally."""
    # Create a request with HTMX headers to a public path
    request = request_factory.get("/public/")
    request.headers = {"HX-Request": "true"}
    request.path = "/public/"

    # Process the request through middleware
    response = middleware(request)

    # Assert that the middleware didn't affect the normal response
    assert response.status_code == 200
    assert "HX-Redirect" not in response.headers
