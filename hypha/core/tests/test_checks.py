from django.test import override_settings

from hypha.core.checks import (
    W001,
    W002,
    W003,
    base_url_not_set,
    primary_host_deprecated,
)


@override_settings(PRIMARY_HOST=None)
def test_no_warning_without_primary_host():
    assert primary_host_deprecated(None) == []


@override_settings(PRIMARY_HOST="apply.example.org")
def test_warns_that_primary_host_is_deprecated():
    assert [warning.id for warning in primary_host_deprecated(None)] == [W001]


@override_settings(PRIMARY_HOST="https://apply.example.org")
def test_warns_when_primary_host_includes_a_scheme():
    assert [warning.id for warning in primary_host_deprecated(None)] == [W001, W002]


@override_settings(WAGTAILADMIN_BASE_URL="https://apply.example.org")
def test_no_warning_when_base_url_is_set():
    assert base_url_not_set(None) == []


@override_settings(WAGTAILADMIN_BASE_URL=None)
def test_warns_when_base_url_is_not_set():
    assert [warning.id for warning in base_url_not_set(None)] == [W003]
