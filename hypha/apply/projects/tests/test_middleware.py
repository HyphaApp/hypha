from unittest.mock import Mock, patch

import pytest
from django.http import Http404
from django.urls import Resolver404

from hypha.apply.projects.middleware import ProjectsEnabledMiddleware


@pytest.fixture
def middleware():
    get_response_mock = Mock()
    return ProjectsEnabledMiddleware(get_response_mock), get_response_mock


@pytest.mark.parametrize(
    "projects_enabled,namespaces,path,should_raise_404",
    [
        # When projects are enabled, project URLs are accessible
        (True, ["projects"], "/projects/some/path/", False),
        # When projects are disabled, project URLs raise Http404
        (False, ["projects"], "/projects/some/path/", True),
        # When projects are disabled, non-project URLs are still accessible
        (False, ["submissions"], "/submissions/path/", False),
        # Nested projects namespaces are properly handled
        (False, ["funds", "projects"], "/funds/projects/some/path/", True),
        # Projects in nested namespaces are accessible when enabled
        (True, ["funds", "projects"], "/funds/projects/some/path/", False),
    ],
)
def test_projects_middleware_access_control(
    middleware, rf, settings, projects_enabled, namespaces, path, should_raise_404
):
    """
    Test that middleware controls access to project URLs based on settings.PROJECTS_ENABLED
    """
    # Setup
    settings.PROJECTS_ENABLED = projects_enabled
    middleware_instance, get_response_mock = middleware
    request = rf.get(path)

    with patch("hypha.apply.projects.middleware.resolve") as mock_resolve:
        resolver_match = Mock(namespaces=namespaces, url_name="project-detail")
        mock_resolve.return_value = resolver_match

        # Execute
        if should_raise_404:
            with pytest.raises(Http404) as excinfo:
                middleware_instance(request)
            assert str(excinfo.value) == "Projects functionality is disabled"
            get_response_mock.assert_not_called()
        else:
            response = middleware_instance(request)
            get_response_mock.assert_called_once_with(request)
            assert response == get_response_mock.return_value

        # Verify resolve was called only if projects are disabled
        if projects_enabled:
            mock_resolve.assert_not_called()
        else:
            mock_resolve.assert_called_once_with(request.path)


def test_resolver404_passes_through(middleware, rf, settings):
    """
    Test that Resolver404 exceptions are caught and handled properly
    (letting Django handle them as it normally would).
    """
    middleware_instance, get_response_mock = middleware
    request = rf.get("/nonexistent/path/")

    settings.PROJECTS_ENABLED = False

    with patch("hypha.apply.projects.middleware.resolve") as mock_resolve:
        mock_resolve.side_effect = Resolver404()

        response = middleware_instance(request)

        mock_resolve.assert_called_once_with(request.path)
        get_response_mock.assert_called_once_with(request)
        assert response == get_response_mock.return_value


@pytest.mark.parametrize(
    "namespaces_value",
    [
        # Empty namespaces list
        [],
        # No namespaces attribute
        None,
    ],
)
def test_non_project_routes_allowed(middleware, rf, settings, namespaces_value):
    """
    Test that URLs with no namespaces or no namespaces attribute are allowed through.
    """
    settings.PROJECTS_ENABLED = False  # Even when projects are disabled
    middleware_instance, get_response_mock = middleware
    request = rf.get("/some/path/")

    with patch("hypha.apply.projects.middleware.resolve") as mock_resolve:
        if namespaces_value is None:
            # Create a mock without namespaces attribute
            resolver_match = Mock(spec=["url_name"])
        else:
            resolver_match = Mock()
            resolver_match.namespaces = namespaces_value

        mock_resolve.return_value = resolver_match

        response = middleware_instance(request)

        mock_resolve.assert_called_once_with(request.path)
        get_response_mock.assert_called_once_with(request)
        assert response == get_response_mock.return_value
