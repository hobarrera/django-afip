import pytest

from django_afip.factories import get_test_file
from django_afip.factories import TaxPayerFactory
from django_afip.models import AuthTicket


@pytest.fixture
def expired_crt() -> bytes:
    with open(get_test_file("test_expired.crt"), "rb") as crt:
        return crt.read()


@pytest.fixture
def expired_key() -> bytes:
    with open(get_test_file("test_expired.key"), "rb") as key:
        return key.read()


@pytest.mark.live
@pytest.fixture(scope="session")
def live_taxpayer(django_db_blocker):
    """Return a taxpayer usable with test servers."""
    with django_db_blocker.unblock():
        taxpayer = TaxPayerFactory.build(pk=1)

    return taxpayer


@pytest.mark.live
@pytest.fixture(scope="session")
def live_ticket(django_db_blocker, live_taxpayer):
    """Return a ticket usable with test servers."""
    with django_db_blocker.unblock():
        ticket = AuthTicket.objects.get_any_active("wsfe")

    return ticket


@pytest.mark.live
@pytest.fixture(scope="class")
def set_live_afip_token(django_db_blocker, live_taxpayer, live_ticket, request):
    """Return a function which saves a valid live ticket into the DB.

    Since AFIP rate-limits how often authentication tokens can be fetched, we
    need to keep one between tests. This fixture creates a taxpayer and ticket
    once per sessions, and provides a helper to store this into the database
    again when needed.
    """

    def inner(self=None):
        with django_db_blocker.unblock():
            live_taxpayer.save()
            live_ticket.owner = live_taxpayer
            live_ticket.save()

    request.cls.set_live_afip_token = inner
    return inner
