# This file is used to setup the django environment for pytest
import pytest
from django.core.management import call_command


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Create initial groups before running tests."""
    with django_db_blocker.unblock():
        call_command("sync_roles")
