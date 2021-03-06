from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from django.test import TestCase
from pytest_django.asserts import assertQuerysetEqual

from django_afip import exceptions
from django_afip import factories
from django_afip import models
from testapp.testmain.tests.testcases import PopulatedLiveAfipTestCase


def test_default_receipt_queryset():
    assert isinstance(models.Receipt.objects.all(), models.ReceiptQuerySet)


@pytest.mark.django_db
def test_validate():
    receipt = factories.ReceiptFactory()
    queryset = models.Receipt.objects.filter(pk=receipt.pk)
    ticket = MagicMock()

    with patch(
        "django_afip.models.ReceiptQuerySet._assign_numbers",
        spec=True,
    ) as mocked_assign_numbers, patch(
        "django_afip.models.ReceiptQuerySet._validate",
        spec=True,
    ) as mocked__validate:
        queryset.validate(ticket)

    assert mocked_assign_numbers.call_count == 1
    assert mocked__validate.call_count == 1
    assert mocked__validate.call_args == call(ticket)


# TODO: Also another tests that checks that we only pass filtered-out receipts.


def test_default_receipt_manager():
    assert isinstance(models.Receipt.objects, models.ReceiptManager)


@pytest.mark.django_db
def test_validate_receipt():
    receipt = factories.ReceiptFactory()
    ticket = MagicMock()
    ticket._called = False

    def fake_validate(qs, ticket=None):
        assertQuerysetEqual(qs, [receipt.pk], lambda r: r.pk)
        ticket._called = True

    with patch(
        "django_afip.models.ReceiptQuerySet.validate",
        fake_validate,
    ):
        receipt.validate(ticket)

    assert ticket._called is True


class ReceiptSuccessfulValidateTestCase(PopulatedLiveAfipTestCase):
    def create_receipt(self, receipt_type_code=6) -> models.Receipt:
        """Create a receipt use for tests. Default type is Factura B."""

        receipt = factories.ReceiptFactory(
            point_of_sales=models.PointOfSales.objects.first(),
            receipt_type__code=receipt_type_code,
        )
        factories.VatFactory(vat_type__code=5, receipt=receipt)
        factories.TaxFactory(tax_type__code=3, receipt=receipt)

        return receipt

    def test_validate_invoice(self):
        """Test validating valid receipts."""

        receipt = self.create_receipt()
        errs = receipt.validate()

        assert len(errs) == 0
        assert receipt.validation.result == models.ReceiptValidation.RESULT_APPROVED
        assert models.ReceiptValidation.objects.count() == 1

    def test_validate_credit_note(self):
        """Test validating valid receipts."""

        # Create a receipt (this credit note relates to it):
        receipt = self.create_receipt()
        errs = receipt.validate()
        assert len(errs) == 0

        # Create a credit note for the above receipt:
        credit_note = self.create_receipt(receipt_type_code=8)  # Nota de Crédito B
        credit_note.related_receipts.add(receipt)
        credit_note.save()

        credit_note.validate(raise_=True)
        assert credit_note.receipt_number is not None


class ReceiptFailedValidateTestCase(PopulatedLiveAfipTestCase):
    def setUp(self):
        super().setUp()
        self.receipt = factories.ReceiptFactory(
            document_type__code=80,
            point_of_sales=models.PointOfSales.objects.first(),
        )
        factories.VatFactory(vat_type__code=5, receipt=self.receipt)
        factories.TaxFactory(tax_type__code=3, receipt=self.receipt)

    def test_failed_validation(self):
        """Test validating valid receipts."""
        errs = self.receipt.validate()

        self.assertEqual(len(errs), 1)
        # FIXME: We're not creating rejection entries
        # self.assertEqual(len(errs), 1)
        # self.assertEqual(
        #     receipt.validation.result,
        #     models.ReceiptValidation.RESULT_REJECTED,
        # )
        self.assertEqual(models.ReceiptValidation.objects.count(), 0)

    def test_raise_validation(self):
        """Test validating valid receipts."""

        with self.assertRaisesRegex(
            exceptions.ValidationError,
            # Note: AFIP apparently edited this message and added a typo:
            "DocNro 203012345 no se encuentra registrado en los padrones",
        ):
            self.receipt.validate(raise_=True)

        # FIXME: We're not creating rejection entries
        # self.assertEqual(
        #     receipt.validation.result,
        #     models.ReceiptValidation.RESULT_REJECTED,
        # )
        self.assertEqual(models.ReceiptValidation.objects.count(), 0)


class ReceiptDataFetchTestCase(PopulatedLiveAfipTestCase):
    def test_fetch_existing_data(self):
        pos = models.PointOfSales.objects.first()
        rt = models.ReceiptType.objects.get(code=6)
        # last receipt number is needed for testing, it seems they flush old receipts
        # so we can't use a fixed receipt number
        last_receipt_number = models.Receipt.objects.fetch_last_receipt_number(pos, rt)
        receipt = models.Receipt.objects.fetch_receipt_data(
            receipt_type=6, receipt_number=last_receipt_number, point_of_sales=pos
        )

        assert receipt.CbteDesde == last_receipt_number
        assert receipt.PtoVta == pos.number


@pytest.mark.django_db
def test_receipt_is_validted_when_not_validated():
    receipt = factories.ReceiptFactory()
    assert not receipt.is_validated


@pytest.mark.django_db
def test_receipt_is_validted_when_validated():
    receipt = factories.ReceiptFactory(receipt_number=1)
    factories.ReceiptValidationFactory(receipt=receipt)
    assert receipt.is_validated


@pytest.mark.django_db
def test_receipt_is_validted_when_failed_validation():
    # These should never really exist,but oh well:
    receipt = factories.ReceiptFactory()
    factories.ReceiptValidationFactory(
        receipt=receipt,
        result=models.ReceiptValidation.RESULT_REJECTED,
    )
    assert not receipt.is_validated

    receipt = factories.ReceiptFactory(receipt_number=1)
    factories.ReceiptValidationFactory(
        receipt=receipt,
        result=models.ReceiptValidation.RESULT_REJECTED,
    )
    assert not receipt.is_validated


@pytest.mark.django_db
def test_default_currency_no_currencies():
    receipt = models.Receipt()
    with pytest.raises(models.CurrencyType.DoesNotExist):
        receipt.currency


@pytest.mark.django_db
def test_default_currency_multieple_currencies():
    c1 = factories.CurrencyTypeFactory(pk=2)
    c2 = factories.CurrencyTypeFactory(pk=1)
    c3 = factories.CurrencyTypeFactory(pk=3)

    receipt = models.Receipt()
    assert receipt.currency != c1
    assert receipt.currency == c2
    assert receipt.currency != c3


class ReceiptTotalVatTestCase(TestCase):
    def test_no_vat(self):
        receipt = factories.ReceiptFactory()

        self.assertEqual(receipt.total_vat, 0)

    def test_multiple_vats(self):
        receipt = factories.ReceiptFactory()
        factories.VatFactory(receipt=receipt)
        factories.VatFactory(receipt=receipt)

        self.assertEqual(receipt.total_vat, 42)

    def test_proper_filtering(self):
        receipt = factories.ReceiptFactory()
        factories.VatFactory(receipt=receipt)
        factories.VatFactory()

        self.assertEqual(receipt.total_vat, 21)


class ReceiptTotalTaxTestCase(TestCase):
    def test_no_tax(self):
        receipt = factories.ReceiptFactory()

        self.assertEqual(receipt.total_tax, 0)

    def test_multiple_taxes(self):
        receipt = factories.ReceiptFactory()
        factories.TaxFactory(receipt=receipt)
        factories.TaxFactory(receipt=receipt)

        self.assertEqual(receipt.total_tax, 18)

    def test_proper_filtering(self):
        receipt = factories.ReceiptFactory()
        factories.TaxFactory(receipt=receipt)
        factories.TaxFactory()

        self.assertEqual(receipt.total_tax, 9)


class CurrencyTypeStrTestCase(TestCase):
    def test_success(self):
        currency_type = models.CurrencyType(
            code="011",
            description="Pesos Uruguayos",
        )
        self.assertEqual(str(currency_type), "Pesos Uruguayos (011)")
