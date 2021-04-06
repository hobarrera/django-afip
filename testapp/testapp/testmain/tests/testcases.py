import pytest
from django.test import TestCase

from django_afip import models


@pytest.mark.live
@pytest.mark.usefixtures("set_live_afip_token")
class LiveAfipTestCase(TestCase):
    """
    Base class for AFIP-WS related tests.

    Since AFIP rate-limits how often authentication tokens can be fetched, we
    need to keep one between tests.
    This class is a simple hack to keep that ticket in-memory and saves it into
    the DB every time a new class is ``setUp``.
    """

    ticket = None

    def setUp(self):
        """Save a TaxPayer and Ticket into the database."""

        self.set_live_afip_token()


class PopulatedLiveAfipTestCase(LiveAfipTestCase):
    def setUp(self):
        """Populate AFIP metadata and create a TaxPayer and PointOfSales."""
        super().setUp()
        models.load_metadata()
        taxpayer = models.TaxPayer.objects.first()
        taxpayer.fetch_points_of_sales()
