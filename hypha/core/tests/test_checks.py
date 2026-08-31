from django.test import override_settings

from hypha.core.checks import W001, W002, primary_host_deprecated


@override_settings(PRIMARY_HOST=None)
def test_no_warning_without_primary_host():
    assert primary_host_deprecated(None) == []


@override_settings(PRIMARY_HOST="apply.example.org")
def test_warns_that_primary_host_is_deprecated():
    assert [warning.id for warning in primary_host_deprecated(None)] == [W001]


@override_settings(PRIMARY_HOST="https://apply.example.org")
def test_warns_when_primary_host_includes_a_scheme():
    assert [warning.id for warning in primary_host_deprecated(None)] == [W001, W002]
