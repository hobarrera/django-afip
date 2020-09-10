from __future__ import annotations

import base64
import logging
import os
import random
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from io import BytesIO
from tempfile import NamedTemporaryFile
from typing import BinaryIO
from typing import List
from typing import NoReturn
from typing import Optional
from typing import Type
from uuid import uuid4

import pytz
from django.conf import settings
from django.core import management
from django.core.files import File
from django.core.files.storage import Storage
from django.db import models
from django.db.models import Count
from django.db.models import Sum
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from django_renderpdf.helpers import render_pdf
from lxml import etree
from lxml.builder import E
from OpenSSL.crypto import FILETYPE_PEM
from OpenSSL.crypto import load_certificate
from OpenSSL.crypto import X509
from zeep.exceptions import Fault

from . import clients
from . import crypto
from . import exceptions
from . import parsers
from . import serializers

logger = logging.getLogger(__name__)
TZ_AR = pytz.timezone(pytz.country_timezones["ar"][0])


# http://www.afip.gov.ar/afip/resol1415_anexo2.html
VAT_CONDITIONS = (
    "IVA Responsable Inscripto",
    "IVA Responsable No Inscripto",
    "IVA Exento",
    "No Responsable IVA",
    "Responsable Monotributo",
)
# NOTE: If you find a VAT condition not listed here, please open an issue, and
# a reference to where it's defined.
CLIENT_VAT_CONDITIONS = (
    "IVA Responsable Inscripto",
    "IVA Responsable No Inscripto",
    "IVA Sujeto Exento",
    "Consumidor Final",
    "Responsable Monotributo",
    "Proveedor del Exterior",
    "Cliente del Exterior",
    "IVA Liberado - Ley Nº 19.640",
    "IVA Responsable Inscripto - Agente de Percepción",
    "Monotributista Social",
    "IVA no alcanzado",
)


def load_metadata() -> NoReturn:
    """Loads metadata from fixtures into the database."""

    for model in GenericAfipType.SUBCLASSES:
        label = model._meta.label.split(".")[1].lower()
        management.call_command("loaddata", label, app="afip")


def check_response(response) -> NoReturn:
    """
    Check that a response is not an error.

    AFIP allows us to create valid tickets with invalid key/CUIT pairs, so we
    can end up with tickets that fail on any service.

    Due to how zeep works, we can't quite catch these sort of errors on some
    middleware level (well, honestly, we need to do a large refactor).

    This method checks if responses have an error, and raise a readable
    message.
    """
    if response.Errors:
        raise exceptions.AfipException(response)


def first_currency() -> Optional[int]:
    """
    Returns the id for the first currency

    The `default` parameter of a foreign key *MUST* be a primary key (and not
    an instance), else migrations break. This helper method exists solely for
    that purpose.
    """
    ct = CurrencyType.objects.filter(code="PES").first()
    if ct:
        return ct.pk


def _get_storage_from_settings(setting_name: str = None) -> Storage:
    path = getattr(settings, setting_name, None)
    if not path:
        return import_string(settings.DEFAULT_FILE_STORAGE)()
    return import_string(path)


class GenericAfipTypeManager(models.Manager):
    """Default Manager for GenericAfipType."""

    def __init__(self, service_name: str, type_name: str):
        """
        Create a new Manager instance for a GenericAfipType.

        This should generally only be required to manually populate a single
        type with upstream data.
        """
        super().__init__()
        self.__service_name = service_name
        self.__type_name = type_name

    def populate(self, ticket: AuthTicket = None) -> NoReturn:
        """Fetch and save data for this model from AFIP's WS.

        Direct usage of this method is discouraged, use
        :func:`~.models.load_metadata` instead.
        """
        ticket = ticket or AuthTicket.objects.get_any_active("wsfe")
        client = clients.get_client("wsfe", ticket.owner.is_sandboxed)
        service = getattr(client.service, self.__service_name)
        response_xml = service(serializers.serialize_ticket(ticket))

        check_response(response_xml)

        for result in getattr(response_xml.ResultGet, self.__type_name):
            self.get_or_create(
                code=result.Id,
                description=result.Desc,
                valid_from=parsers.parse_date(result.FchDesde),
                valid_to=parsers.parse_date(result.FchHasta),
            )

    def get_by_natural_key(self, code):
        return self.get(code=code)

    def exists_by_natural_key(self, code):
        return self.filter(code=code).exists()


class GenericAfipType(models.Model):
    """An abstract class for several of AFIP's metadata types.

    You should not use this class directly, only subclasses of it. You should
    not create subclasses of this model unless you really know what you're doing.
    """

    SUBCLASSES: List[Type] = []

    def __init_subclass__(cls, **kwargs):
        """Keeps a registry of known subclasses."""
        super().__init_subclass__(**kwargs)
        GenericAfipType.SUBCLASSES.append(cls)

    code = models.CharField(
        _("code"),
        max_length=3,
    )
    description = models.CharField(
        _("description"),
        max_length=250,
    )
    valid_from = models.DateField(
        _("valid from"),
        null=True,
        blank=True,
    )
    valid_to = models.DateField(
        _("valid until"),
        null=True,
        blank=True,
    )

    def natural_key(self):
        return (self.code,)

    def __str__(self):
        return self.description

    class Meta:
        abstract = True


class ReceiptType(GenericAfipType):
    """An AFIP receipt type.

    See the AFIP's documentation for details on each receipt type.
    """

    objects = GenericAfipTypeManager("FEParamGetTiposCbte", "CbteTipo")

    class Meta:
        verbose_name = _("receipt type")
        verbose_name_plural = _("receipt types")


class ConceptType(GenericAfipType):
    """
    An AFIP concept type.

    See the AFIP's documentation for details on each concept type.
    """

    objects = GenericAfipTypeManager("FEParamGetTiposConcepto", "ConceptoTipo")

    class Meta:
        verbose_name = _("concept type")
        verbose_name_plural = _("concept types")


class DocumentType(GenericAfipType):
    """
    An AFIP document type.

    See the AFIP's documentation for details on each document type.
    """

    objects = GenericAfipTypeManager("FEParamGetTiposDoc", "DocTipo")

    class Meta:
        verbose_name = _("document type")
        verbose_name_plural = _("document types")


class VatType(GenericAfipType):
    """
    An AFIP VAT type.

    See the AFIP's documentation for details on each VAT type.
    """

    objects = GenericAfipTypeManager("FEParamGetTiposIva", "IvaTipo")

    class Meta:
        verbose_name = _("vat type")
        verbose_name_plural = _("vat types")


class TaxType(GenericAfipType):
    """
    An AFIP tax type.

    See the AFIP's documentation for details on each tax type.
    """

    objects = GenericAfipTypeManager("FEParamGetTiposTributos", "TributoTipo")

    class Meta:
        verbose_name = _("tax type")
        verbose_name_plural = _("tax types")


class CurrencyType(GenericAfipType):
    """
    An AFIP curreny type.

    See the AFIP's documentation for details on each currency type.
    """

    objects = GenericAfipTypeManager("FEParamGetTiposMonedas", "Moneda")

    def __str__(self):
        return "{} ({})".format(self.description, self.code)

    class Meta:
        verbose_name = _("currency type")
        verbose_name_plural = _("currency types")


class TaxPayer(models.Model):
    """
    Represents an AFIP TaxPayer.

    Note that multiple instances of this object can actually represent the same
    taxpayer, each using a different key.

    The following fields are only used for generating printables, and are never
    sent to AFIP, hence, are entirely optional:

    - logo
    """

    name = models.CharField(
        _("name"),
        max_length=32,
        help_text=_("A friendly name to recognize this taxpayer."),
    )
    key = models.FileField(
        verbose_name=_("key"),
        upload_to="afip/taxpayers/keys/",
        storage=_get_storage_from_settings("AFIP_KEY_STORAGE"),
        blank=True,
        null=True,
    )
    certificate = models.FileField(
        verbose_name=_("certificate"),
        upload_to="afip/taxpayers/certs/",
        storage=_get_storage_from_settings("AFIP_CERT_STORAGE"),
        blank=True,
        null=True,
    )
    cuit = models.BigIntegerField(
        _("cuit"),
    )
    is_sandboxed = models.BooleanField(
        _("is sandboxed"),
        help_text=_(
            "Indicates if this taxpayer should use with the sandbox servers "
            "rather than the production servers."
        ),
    )
    certificate_expiration = models.DateTimeField(
        _("certificate expiration"),
        editable=False,
        null=True,  # Either no cert, or and old TaxPayer
        help_text=_(
            "Stores expiration for the current certificate.<br>Note that this "
            "field is updated pre-save, so the value may be invalid for unsaved models."
        ),
    )
    active_since = models.DateField(
        _("active since"),
        help_text=_("Date since which this taxpayer has been legally active."),
    )
    logo = models.ImageField(
        verbose_name=_("logo"),
        upload_to="afip/taxpayers/logos/",
        storage=_get_storage_from_settings("AFIP_LOGO_STORAGE"),
        blank=True,
        null=True,
        help_text=_("A logo to use when generating printable receipts."),
    )

    @property
    def logo_as_data_uri(self):
        """This TaxPayer's logo as a data uri."""
        _, ext = os.path.splitext(self.logo.file.name)
        with self.logo.open() as f:
            data = base64.b64encode(f.read())

        return "data:image/{};base64,{}".format(
            ext[1:], data.decode()  # Remove the leading dot.
        )

    @property
    def certificate_object(self) -> X509:
        """
        Returns the certificate as an OpenSSL object

        Returns the certificate as an OpenSSL object (rather than as a file
        object).
        """

        if not self.certificate:
            return None
        self.certificate.seek(0)
        return load_certificate(FILETYPE_PEM, self.certificate.read())

    def get_certificate_expiration(self) -> datetime:
        """
        Gets the certificate expiration from the certificate


        Gets the certificate expiration from the certificate file. Note that
        this value is stored into ``certificate_expiration`` when an instance
        is saved, so you should generally prefer that method (since this one
        requires reading and parsing the entire certificate).
        """
        datestring = self.certificate_object.get_notAfter().decode()
        dt = datetime.strptime(datestring, "%Y%m%d%H%M%SZ")
        return dt.replace(tzinfo=timezone.utc)

    def generate_key(self, force=False) -> bool:
        """
        Creates a key file for this TaxPayer

        Creates a key file for this TaxPayer if it does not have one, and
        immediately saves it.

        A new key will not be generated if one is already set, unless the ``force``
        parameter is true. This is to prevent overwriting a potentially in-use key.

        Returns True if and only if a key was created.
        """
        if self.key and not force:
            logger.warning("Tried to generate key for a taxpayer that already had one")
            return False

        with NamedTemporaryFile(suffix=".key") as file_:
            crypto.create_key(file_)
            self.key = File(file_, name="{}.key".format(uuid4().hex))
            self.save()

        return True

    def generate_csr(self, basename="djangoafip") -> BinaryIO:
        """
        Creates a CSR for this TaxPayer's key

        Creates a file-like object that contains the CSR which can be used to
        request a new certificate from AFIP.
        """
        csr = BytesIO()
        crypto.create_csr(
            self.key.file,
            self.name,
            "{}{}".format(basename, int(datetime.now().timestamp())),
            "CUIT {}".format(self.cuit),
            csr,
        )
        csr.seek(0)
        return csr

    def create_ticket(self, service: str) -> AuthTicket:
        """Create an AuthTicket for a given service."""
        ticket = AuthTicket(owner=self, service=service)
        ticket.authorize()
        return ticket

    def get_ticket(self, service: str) -> Optional[AuthTicket]:
        """Return an existing AuthTicket for a given service, if any."""
        return self.auth_tickets.filter(
            expires__gt=datetime.now(timezone.utc),
            service=service,
        ).last()

    def get_or_create_ticket(self, service: str):
        """
        Return or create a new AuthTicket for a given serivce.

        Return an existing ticket for a service if one is available, otherwise,
        create a new one and return that.

        This is generally the preferred method of obtaining tickets for any
        service.
        """
        return self.get_ticket(service) or self.create_ticket(service)

    def fetch_points_of_sales(self, ticket: AuthTicket = None):
        """
        Fetch all point of sales objects.

        Fetch all point of sales from the WS and store (or update) them
        locally.

        Returns a list of tuples with the format (pos, created,).
        """
        ticket = ticket or self.get_or_create_ticket("wsfe")

        client = clients.get_client("wsfe", self.is_sandboxed)
        response = client.service.FEParamGetPtosVenta(
            serializers.serialize_ticket(ticket),
        )
        check_response(response)

        results = []
        for pos_data in response.ResultGet.PtoVenta:
            results.append(
                PointOfSales.objects.update_or_create(
                    number=pos_data.Nro,
                    owner=self,
                    defaults={
                        "issuance_type": pos_data.EmisionTipo,
                        "blocked": pos_data.Bloqueado == "N",
                        "drop_date": parsers.parse_date(pos_data.FchBaja),
                    },
                )
            )

        return results

    def __repr__(self):
        return "<TaxPayer {}: {}, CUIT {}>".format(
            self.pk,
            self.name,
            self.cuit,
        )

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = _("taxpayer")
        verbose_name_plural = _("taxpayers")


class TaxPayerProfile(models.Model):
    """
    Metadata about a taxpayer used for printable receipts.

    None of this information is required or sent to the AFIP when notifying
    about receipt generation. It is used *only* for PDF generation.

    Most of these can be overriden per-receipt as this class is a placeholder
    for default values.
    """

    taxpayer = models.OneToOneField(
        TaxPayer,
        related_name="profile",
        verbose_name=_("taxpayer"),
        on_delete=models.CASCADE,
    )
    issuing_name = models.CharField(
        max_length=128,
        verbose_name=_("issuing name"),
        help_text=_("The name of the issuing entity as shown on receipts."),
    )
    issuing_address = models.TextField(
        _("issuing address"),
        help_text=_("The address of the issuing entity as shown on receipts."),
    )
    issuing_email = models.CharField(
        max_length=128,
        verbose_name=_("issuing email"),
        blank=True,
        null=True,
        help_text=_("The email of the issuing entity as shown on receipts."),
    )
    vat_condition = models.CharField(
        max_length=48,
        choices=(
            (
                condition,
                condition,
            )
            for condition in VAT_CONDITIONS
        ),
        verbose_name=_("vat condition"),
    )
    gross_income_condition = models.CharField(
        max_length=48,
        verbose_name=_("gross income condition"),
    )
    sales_terms = models.CharField(
        max_length=48,
        verbose_name=_("sales terms"),
        help_text=_(
            "The terms of the sale printed onto receipts by default "
            "(eg: single payment, checking account, etc)."
        ),
    )

    def __str__(self):
        return f"<TaxPayerProfile for TaxPayer {self.pk}>"

    class Meta:
        verbose_name = _("taxpayer profile")
        verbose_name_plural = _("taxpayer profiles")


class PointOfSales(models.Model):
    """
    Represents an existing AFIP point of sale.

    Points of sales need to be created via AFIP's web interface and it is
    recommended that you use :meth:`~.TaxPayer.fetch_points_of_sales` to fetch
    these programatically.

    Note that deleting or altering these models will not affect upstream point
    of sales.
    """

    number = models.PositiveSmallIntegerField(
        _("number"),
    )
    issuance_type = models.CharField(
        _("issuance type"),
        max_length=24,
        help_text="Indicates if this POS emits using CAE and CAEA.",
    )
    blocked = models.BooleanField(
        _("blocked"),
    )
    drop_date = models.DateField(
        _("drop date"),
        null=True,
        blank=True,
    )

    owner = models.ForeignKey(
        TaxPayer,
        related_name="points_of_sales",
        verbose_name=_("owner"),
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return str(self.number)

    class Meta:
        unique_together = (("number", "owner"),)
        verbose_name = _("point of sales")
        verbose_name_plural = _("points of sales")


class AuthTicketManager(models.Manager):
    def get_any_active(self, service: str) -> AuthTicket:
        ticket = AuthTicket.objects.filter(
            token__isnull=False,
            expires__gt=datetime.now(timezone.utc),
            service=service,
        ).first()
        if ticket:
            return ticket

        taxpayer = TaxPayer.objects.order_by("?").first()

        if not taxpayer:
            raise exceptions.AuthenticationError(
                _("There are no taxpayers to generate a ticket."),
            )

        return taxpayer.create_ticket(service)


class AuthTicket(models.Model):
    """An AFIP Authorization ticket.

    This is a signed ticket used to communicate with AFIP's webservices.

    Applications should not generally have to deal with these tickets
    themselves; most services will find or create one as necessary.
    """

    @staticmethod
    def default_generated() -> datetime:
        return datetime.now(TZ_AR)

    @staticmethod
    def default_expires() -> datetime:
        tomorrow = datetime.now(TZ_AR) + timedelta(hours=12)
        return tomorrow

    @staticmethod
    def default_unique_id() -> int:
        return random.randint(0, 2147483647)

    owner = models.ForeignKey(
        TaxPayer,
        verbose_name=_("owner"),
        related_name="auth_tickets",
        on_delete=models.CASCADE,
    )
    unique_id = models.IntegerField(
        _("unique id"),
        default=default_unique_id,
    )
    generated = models.DateTimeField(
        _("generated"),
        default=default_generated,
    )
    expires = models.DateTimeField(
        _("expires"),
        default=default_expires,
    )
    service = models.CharField(
        _("service"),
        max_length=6,
        help_text=_("Service for which this ticket has been authorized."),
    )

    token = models.TextField(
        _("token"),
    )
    signature = models.TextField(
        _("signature"),
    )

    objects = AuthTicketManager()

    TOKEN_XPATH = "/loginTicketResponse/credentials/token"
    SIGN_XPATH = "/loginTicketResponse/credentials/sign"

    def __create_request_xml(self):
        request_xml = E.loginTicketRequest(
            {"version": "1.0"},
            E.header(
                E.uniqueId(str(self.unique_id)),
                E.generationTime(serializers.serialize_datetime(self.generated)),
                E.expirationTime(serializers.serialize_datetime(self.expires)),
            ),
            E.service(self.service),
        )
        return etree.tostring(request_xml, pretty_print=True)

    def __sign_request(self, request):
        with self.owner.certificate.file.open("rb") as f:
            cert = f.read()

        with self.owner.key.file.open("rb") as f:
            key = f.read()

        return crypto.create_embeded_pkcs7_signature(request, cert, key)

    def authorize(self) -> NoReturn:
        """Send this ticket to AFIP for authorization."""
        request = self.__create_request_xml()
        request = self.__sign_request(request)
        request = base64.b64encode(request).decode()

        client = clients.get_client("wsaa", self.owner.is_sandboxed)
        try:
            raw_response = client.service.loginCms(request)
        except Fault as e:
            if str(e) == "Certificado expirado":
                raise exceptions.CertificateExpired(str(e)) from e
            if str(e) == "Certificado no emitido por AC de confianza":
                raise exceptions.UntrustedCertificate(str(e)) from e
            raise exceptions.AuthenticationError(str(e)) from e
        response = etree.fromstring(raw_response.encode("utf-8"))

        self.token = response.xpath(self.TOKEN_XPATH)[0].text
        self.signature = response.xpath(self.SIGN_XPATH)[0].text

        self.save()

    def __str__(self):
        return str(self.unique_id)

    class Meta:
        verbose_name = _("authorization ticket")
        verbose_name_plural = _("authorization tickets")


class ReceiptQuerySet(models.QuerySet):
    """The default queryset obtains when querying via :class:`~.ReceiptManager`."""

    def _assign_numbers(self) -> NoReturn:
        """Assign numbers in preparation for validating these receipts.

        WARNING: Don't call the method manually unless you know what you're
        doing!
        """
        first = self.select_related("point_of_sales", "receipt_type").first()

        next_num = (
            Receipt.objects.fetch_last_receipt_number(
                first.point_of_sales,
                first.receipt_type,
            )
            + 1
        )

        for receipt in self.filter(receipt_number__isnull=True):
            # Atomically update receipt number
            Receipt.objects.filter(pk=receipt.id, receipt_number__isnull=True,).update(
                receipt_number=next_num,
            )
            next_num += 1

    def check_groupable(self):
        """Check that all receipts returned by this queryset are groupable.

        "Groupable" means that they can be validated together: they have the
        same POS and receipt type.

        Returns the same queryset is all receipts are groupable, otherwise,
        raises :class:`~.CannotValidateTogether`.
        """
        types = self.aggregate(
            poses=Count(
                "point_of_sales_id",
            ),
            types=Count("receipt_type"),
        )

        if set(types.values()) > {1}:
            raise exceptions.CannotValidateTogether()

        return self

    def validate(self, ticket: AuthTicket = None):
        """Validate all receipts matching this queryset.

        Note that, due to how AFIP implements its numbering, this method is not
        thread-safe, or even multiprocess-safe.

        Because of this, it is possible that not all instances matching this
        queryset are validated properly. Obviously, only successfully validated
        receipts will be updated.

        Returns a list of errors as returned from AFIP's webservices. An
        exception is not raised because partial failures are possible.

        Receipts that succesfully validate will have a
        :class:`~.ReceiptValidation` object attatched to them with a validation
        date and CAE information.

        Already-validated receipts are ignored.

        Attempting to validate an empty queryset will simply return an empty
        list.
        """
        # Skip any already-validated ones:
        qs = self.filter(validation__isnull=True).check_groupable()
        if qs.count() == 0:
            return []
        qs.order_by("issued_date", "id")._assign_numbers()

        return qs._validate(ticket)

    def _validate(self, ticket=None):
        first = self.first()
        ticket = ticket or first.point_of_sales.owner.get_or_create_ticket("wsfe")
        client = clients.get_client("wsfe", first.point_of_sales.owner.is_sandboxed)
        response = client.service.FECAESolicitar(
            serializers.serialize_ticket(ticket),
            serializers.serialize_multiple_receipts(self),
        )
        check_response(response)
        errs = []
        for cae_data in response.FeDetResp.FECAEDetResponse:
            if cae_data.Resultado == ReceiptValidation.RESULT_APPROVED:
                validation = ReceiptValidation.objects.create(
                    result=cae_data.Resultado,
                    cae=cae_data.CAE,
                    cae_expiration=parsers.parse_date(cae_data.CAEFchVto),
                    receipt=self.get(
                        receipt_number=cae_data.CbteDesde,
                    ),
                    processed_date=parsers.parse_datetime(
                        response.FeCabResp.FchProceso,
                    ),
                )
                if cae_data.Observaciones:
                    for obs in cae_data.Observaciones.Obs:
                        observation = Observation.objects.create(
                            code=obs.Code,
                            message=obs.Msg,
                        )
                    validation.observations.add(observation)
            elif cae_data.Observaciones:
                for obs in cae_data.Observaciones.Obs:
                    errs.append(
                        "Error {}: {}".format(
                            obs.Code,
                            parsers.parse_string(obs.Msg),
                        )
                    )

        # Remove the number from ones that failed to validate:
        self.filter(validation__isnull=True).update(receipt_number=None)

        return errs


class ReceiptManager(models.Manager):
    """Default manager for the :class:`~.Receipt` class.

    You should generally access this using ``Receipt.objects``.
    """

    def fetch_last_receipt_number(self, point_of_sales, receipt_type):
        """Returns the number for the last validated receipt."""
        client = clients.get_client("wsfe", point_of_sales.owner.is_sandboxed)
        response_xml = client.service.FECompUltimoAutorizado(
            serializers.serialize_ticket(
                point_of_sales.owner.get_or_create_ticket("wsfe")
            ),
            point_of_sales.number,
            receipt_type.code,
        )
        check_response(response_xml)

        # TODO XXX: Error handling
        # (FERecuperaLastCbteResponse){
        #    PtoVta = 0
        #    CbteTipo = 0
        #    CbteNro = 0
        #    Errors =
        #       (ArrayOfErr){
        #          Err[] =
        #             (Err){
        #                Code = 601
        #                Msg = "CUIT representada no incluida en Token"
        #             },
        #       }
        #  }

        return response_xml.CbteNro

    def get_queryset(self):
        return ReceiptQuerySet(self.model, using=self._db).select_related(
            "receipt_type",
        )


class Receipt(models.Model):
    """A receipt, as sent to AFIP.

    Note that AFIP allows sending ranges of receipts, but this isn't generally
    what you want, so we model invoices individually.

    You'll probably want to relate some `Sale` or `Order` object from your
    model with each Receipt.

    All ``document_`` fields contain the recipient's data.

    If the taxpayer has taxes or pays VAT, you need to attach :class:`~.Tax`
    and/or :class:`~.Vat` instances to the Receipt.
    """

    point_of_sales = models.ForeignKey(
        PointOfSales,
        related_name="receipts",
        verbose_name=_("point of sales"),
        on_delete=models.PROTECT,
    )
    receipt_type = models.ForeignKey(
        ReceiptType,
        related_name="receipts",
        verbose_name=_("receipt type"),
        on_delete=models.PROTECT,
    )
    concept = models.ForeignKey(
        ConceptType,
        verbose_name=_("concept"),
        related_name="receipts",
        on_delete=models.PROTECT,
    )
    document_type = models.ForeignKey(
        DocumentType,
        verbose_name=_("document type"),
        related_name="receipts",
        help_text=_("The document type of the recipient of this receipt."),
        on_delete=models.PROTECT,
    )
    document_number = models.BigIntegerField(
        _("document number"),
        help_text=_("The document number of the recipient of this receipt."),
    )
    # NOTE: WS will expect receipt_from and receipt_to.
    receipt_number = models.PositiveIntegerField(
        _("receipt number"),
        null=True,
        blank=True,
        help_text=_(
            "If left blank, the next valid number will assigned when "
            "validating the receipt."
        ),
    )
    issued_date = models.DateField(
        verbose_name=_("issued date"),
        help_text=_("Can diverge up to 5 days for good, or 10 days otherwise."),
    )
    total_amount = models.DecimalField(
        # ImpTotal
        _("total amount"),
        max_digits=15,
        decimal_places=2,
        help_text=_(
            "Must be equal to the sum of net_taxed, exempt_amount, net_taxes, "
            "and all taxes and vats."
        ),
    )
    net_untaxed = models.DecimalField(
        # ImpTotConc
        _("total untaxable amount"),
        max_digits=15,
        decimal_places=2,
        help_text=_(
            "The total amount to which taxes do not apply.<br>"
            "For C-type receipts, this must be zero."
        ),
    )
    net_taxed = models.DecimalField(
        # ImpNeto
        _("total taxable amount"),
        max_digits=15,
        decimal_places=2,
        help_text=_(
            "The total amount to which taxes apply.<br>"
            "For C-type receipts, this is equal to the subtotal."
        ),
    )
    exempt_amount = models.DecimalField(
        # ImpOpEx
        # Sólo para emisores que son IVA exento
        _("exempt amount"),
        max_digits=15,
        decimal_places=2,
        help_text=_(
            "Only for categories which are tax-exempt.<br>"
            "For C-type receipts, this must be zero."
        ),
    )
    service_start = models.DateField(
        _("service start date"),
        help_text=_("Date on which a service started. No applicable for goods."),
        null=True,
        blank=True,
    )
    service_end = models.DateField(
        _("service end date"),
        help_text=_("Date on which a service ended. No applicable for goods."),
        null=True,
        blank=True,
    )
    expiration_date = models.DateField(
        _("receipt expiration date"),
        help_text=_("Date on which this receipt expires. No applicable for goods."),
        null=True,
        blank=True,
    )
    currency = models.ForeignKey(
        CurrencyType,
        verbose_name=_("currency"),
        related_name="documents",
        help_text=_("Currency in which this receipt is issued."),
        on_delete=models.PROTECT,
        default=first_currency,
    )
    currency_quote = models.DecimalField(
        _("currency quote"),
        max_digits=10,
        decimal_places=6,
        default=1,
        help_text=_("The currency's quote on the day this receipt was issued."),
    )
    related_receipts = models.ManyToManyField(
        "Receipt",
        verbose_name=_("related receipts"),
        blank=True,
    )

    objects = ReceiptManager()

    # TODO: Not implemented: optionals
    # TODO: methods to validate totals

    @property
    def total_vat(self) -> int:
        """Returns the sum of all Vat objects."""
        q = Vat.objects.filter(receipt=self).aggregate(total=Sum("amount"))
        return q["total"] or 0

    @property
    def total_tax(self) -> int:
        """Returns the sum of all Tax objects."""
        q = Tax.objects.filter(receipt=self).aggregate(total=Sum("amount"))
        return q["total"] or 0

    @property
    def formatted_number(self) -> Optional[str]:
        """This receipt's number in the usual format: ``0001-00003087``."""
        if self.receipt_number:
            return "{:04d}-{:08d}".format(
                self.point_of_sales.number,
                self.receipt_number,
            )
        return None

    @property
    def is_validated(self) -> bool:
        """True if this instance is validated.

        Note that resolving this property requires a DB query, so if you've a
        very large amount of receipts you should prefetch (see django's
        ``select_related``) the ``validation`` field. Even so, a DB query *may*
        be triggered.

        If you need a large list of validated receipts, you should actually
        filter them via a QuerySet::

            Receipt.objects.filter(validation__result==RESULT_APPROVED)
        """
        # Avoid the DB lookup if possible:
        if not self.receipt_number:
            return False

        try:
            return self.validation.result == ReceiptValidation.RESULT_APPROVED
        except ReceiptValidation.DoesNotExist:
            return False

    def validate(self, ticket: AuthTicket = None, raise_=False):
        """Validates this receipt.

        This is a shortcut to :class:`~.ReceiptQuerySet`'s method of the same
        name. Calling this validates only this instance.

        :param AuthTicket ticket: Use this ticket. If None, one will be loaded
            or created automatically.
        :param bool raise_: If True, an exception will be raised when
            validation fails.
        """
        # XXX: Maybe actually have this sortcut raise an exception?
        rv = Receipt.objects.filter(pk=self.pk).validate(ticket)
        # Since we're operating via a queryset, this instance isn't properly
        # updated:
        self.refresh_from_db()
        if raise_ and rv:
            raise exceptions.ValidationError(rv[0])
        return rv

    def __repr__(self):
        return "<Receipt {}: {} {} for {}>".format(
            self.pk,
            self.receipt_type,
            self.receipt_number,
            self.point_of_sales.owner,
        )

    def __str__(self):
        if self.receipt_number:
            return "{} {}".format(self.receipt_type, self.formatted_number)
        else:
            return _("Unnumbered %s") % self.receipt_type

    class Meta:
        ordering = ("issued_date",)
        verbose_name = _("receipt")
        verbose_name_plural = _("receipts")
        unique_together = [["point_of_sales", "receipt_type", "receipt_number"]]
        # TODO: index_together...


class ReceiptPDFManager(models.Manager):
    def create_for_receipt(self, receipt, **kwargs) -> ReceiptPDF:
        """Creates a ReceiptPDF object for a given receipt.

        Does not actually generate the related PDF file.

        All attributes will be completed with the information for the relevant
        ``TaxPayerProfile`` instance.

        :param Receipt receipt: The receipt for the PDF which will be
            generated.
        """
        try:
            profile = TaxPayerProfile.objects.get(
                taxpayer__points_of_sales__receipts=receipt,
            )
        except TaxPayerProfile.DoesNotExist:
            raise exceptions.DjangoAfipException(
                "Cannot generate a PDF for taxpayer with no profile",
            )
        pdf = ReceiptPDF.objects.create(
            receipt=receipt,
            issuing_name=profile.issuing_name,
            issuing_address=profile.issuing_address,
            issuing_email=profile.issuing_email,
            vat_condition=profile.vat_condition,
            gross_income_condition=profile.gross_income_condition,
            sales_terms=profile.sales_terms,
            **kwargs,
        )
        return pdf


class ReceiptPDF(models.Model):
    """Printable version of a receipt.

    Contains all print-related data of a receipt.

    All ``issuing_*`` fields contain data for the entity issuing the Receipt
    (these may change from one receipt to the next if, for example, the entity
    moved).

    The PDF file itself is saved into the ``pdf_file`` attribute, and is
    generated when saving the model for the first time. If any attributes are
    changed, you should manually call :meth:`~.ReceiptPDF.save_pdf` to
    regenerate the PDF file.

    PDF generation is skipped if the receipt has not been validated.
    """

    def upload_to(self, filename="untitled", instance=None) -> str:
        """
        Returns the full path for generated receipts.

        These are bucketed inside nested directories, to avoid hundreds of
        thousands of children in single directories (which can make reading
        them excessively slow).
        """
        _, extension = os.path.splitext(os.path.basename(filename))
        uuid = uuid4().hex
        buckets = uuid[0:2], uuid[2:4]
        filename = "".join([uuid, extension])

        return os.path.join("afip/receipts", buckets[0], buckets[1], filename)

    receipt = models.OneToOneField(
        Receipt,
        verbose_name=_("receipt"),
        on_delete=models.PROTECT,
    )
    pdf_file = models.FileField(
        verbose_name=_("pdf file"),
        upload_to=upload_to,
        storage=_get_storage_from_settings("AFIP_PDF_STORAGE"),
        blank=True,
        null=True,
        help_text=_("The actual file which contains the PDF data."),
    )
    issuing_name = models.CharField(
        max_length=128,
        verbose_name=_("issuing name"),
    )
    issuing_address = models.TextField(
        _("issuing address"),
    )
    issuing_email = models.CharField(
        max_length=128,
        verbose_name=_("issuing email"),
        blank=True,
        null=True,
    )
    vat_condition = models.CharField(
        max_length=48,
        choices=(
            (
                condition,
                condition,
            )
            for condition in VAT_CONDITIONS
        ),
        verbose_name=_("vat condition"),
    )
    gross_income_condition = models.CharField(
        max_length=48,
        verbose_name=_("gross income condition"),
    )
    client_name = models.CharField(
        max_length=128,
        verbose_name=_("client name"),
    )
    client_address = models.TextField(
        _("client address"),
        blank=True,
    )
    client_vat_condition = models.CharField(
        max_length=48,
        choices=(
            (
                cond,
                cond,
            )
            for cond in CLIENT_VAT_CONDITIONS
        ),
        verbose_name=_("client vat condition"),
    )
    sales_terms = models.CharField(
        max_length=48,
        verbose_name=_("sales terms"),
        help_text=_('Should be something like "Cash", "Payable in 30 days", etc.'),
    )

    objects = ReceiptPDFManager()

    def save_pdf(self, save_model: bool = True) -> NoReturn:
        """
        Save the receipt as a PDF related to this model.

        The related :class:`~.Receipt` should be validated first, of course.
        This model instance must have been saved prior to calling this method.

        :param save_model: If True, immediately save this model instance.
        """
        from django_afip.views import ReceiptPDFView

        if not self.receipt.is_validated:
            raise exceptions.DjangoAfipException(
                _("Cannot generate pdf for non-authorized receipt")
            )

        self.pdf_file = File(BytesIO(), name="{}.pdf".format(uuid4().hex))
        render_pdf(
            template=ReceiptPDFView().get_template_names(self.receipt),
            file_=self.pdf_file,
            context=ReceiptPDFView.get_context_for_pk(self.receipt_id),
        )

        if save_model:
            self.save()

    def __str__(self):
        return _("Receipt PDF for %s") % self.receipt_id

    class Meta:
        verbose_name = _("receipt pdf")
        verbose_name_plural = _("receipt pdfs")


class ReceiptEntry(models.Model):
    """An entry in a receipt.

    Each ReceiptEntry represents a line in printable version of a Receipt. You
    should generally have one instance per product or service.

    Note that each entry has a :class:`~.Vat` because a single Receipt can have
    multiple products with different :class:`~.VatType`.
    """

    receipt = models.ForeignKey(
        Receipt,
        related_name="entries",
        verbose_name=_("receipt"),
        on_delete=models.PROTECT,
    )
    description = models.CharField(
        max_length=128,
        verbose_name=_("description"),
    )
    quantity = models.PositiveSmallIntegerField(
        _("quantity"),
    )
    unit_price = models.DecimalField(
        _("unit price"),
        max_digits=15,
        decimal_places=2,
        help_text=_("Price per unit before vat or taxes."),
    )
    vat = models.ForeignKey(
        VatType,
        related_name="receipt_entries",
        verbose_name=_("vat"),
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )

    @property
    def total_price(self) -> int:
        """The total price for this line (quantity * price)."""
        return self.quantity * self.unit_price

    class Meta:
        verbose_name = _("receipt entry")
        verbose_name_plural = _("receipt entries")


class Tax(models.Model):
    """A tax (type+amount) for a specific Receipt."""

    tax_type = models.ForeignKey(
        TaxType,
        verbose_name=_("tax type"),
        on_delete=models.PROTECT,
    )
    description = models.CharField(
        _("description"),
        max_length=80,
    )
    base_amount = models.DecimalField(
        _("base amount"),
        max_digits=15,
        decimal_places=2,
    )
    aliquot = models.DecimalField(
        _("aliquot"),
        max_digits=5,
        decimal_places=2,
    )
    amount = models.DecimalField(
        _("amount"),
        max_digits=15,
        decimal_places=2,
    )

    receipt = models.ForeignKey(
        Receipt,
        related_name="taxes",
        on_delete=models.PROTECT,
    )

    def compute_amount(self) -> int:
        """Auto-assign and return the total amount for this tax."""
        self.amount = self.base_amount * self.aliquot / 100
        return self.amount

    class Meta:
        verbose_name = _("tax")
        verbose_name_plural = _("taxes")


class Vat(models.Model):
    """A VAT (type+amount) for a specific Receipt."""

    vat_type = models.ForeignKey(
        VatType,
        verbose_name=_("vat type"),
        on_delete=models.PROTECT,
    )
    base_amount = models.DecimalField(
        _("base amount"),
        max_digits=15,
        decimal_places=2,
    )
    amount = models.DecimalField(
        _("amount"),
        max_digits=15,
        decimal_places=2,
    )

    receipt = models.ForeignKey(
        Receipt,
        related_name="vat",
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = _("vat")
        verbose_name_plural = _("vat")


class Observation(models.Model):
    """An observation returned by AFIP.

    AFIP seems to assign re-used codes to Observation, so we actually store
    them as separate objects, and link to them from failed validations.
    """

    code = models.PositiveSmallIntegerField(
        _("code"),
    )
    message = models.CharField(
        _("message"),
        max_length=255,
    )

    class Meta:
        verbose_name = _("observation")
        verbose_name_plural = _("observations")


class ReceiptValidation(models.Model):
    """The validation for a single :class:`~.Receipt`.

    This contains all validation-related data for a receipt, including its CAE
    and the CAE expiration, unless validation has failed.

    The ``observation`` field may contain any data returned by AFIP regarding
    validation failure.
    """

    RESULT_APPROVED = "A"
    RESULT_REJECTED = "R"

    # TODO: replace this with a `successful` boolean field.
    result = models.CharField(
        _("result"),
        max_length=1,
        choices=(
            (RESULT_APPROVED, _("approved")),
            (RESULT_REJECTED, _("rejected")),
        ),
        help_text=_("Indicates whether the validation was succesful or not."),
    )
    processed_date = models.DateTimeField(
        _("processed date"),
    )
    cae = models.CharField(
        _("cae"),
        max_length=14,
        help_text=_("The CAE as returned by the AFIP."),
    )
    cae_expiration = models.DateField(
        _("cae expiration"),
        help_text=_("The CAE expiration as returned by the AFIP."),
    )
    observations = models.ManyToManyField(
        Observation,
        verbose_name=_("observations"),
        related_name="validations",
        help_text=_(
            "The observations as returned by the AFIP. These are generally "
            "present for failed validations."
        ),
    )

    receipt = models.OneToOneField(
        Receipt,
        related_name="validation",
        verbose_name=_("receipt"),
        help_text=_("The Receipt for which this validation applies."),
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return _("Validation for %s. Result: %s") % (
            self.receipt,
            self.get_result_display(),
        )

    def __repr__(self):
        return "<{} {}: {} for Receipt {}>".format(
            self.__class__.__name__,
            self.pk,
            self.result,
            self.receipt_id,
        )

    class Meta:
        verbose_name = _("receipt validation")
        verbose_name_plural = _("receipt validations")
