from typing import List

import django.db.models.deletion
from django.db import migrations
from django.db import models

import django_afip.models


class Migration(migrations.Migration):

    replaces = [
        ("afip", "0001_initial"),
        ("afip", "0002_auto_20150909_1837"),
        ("afip", "0003_vat_tax_digits"),
        ("afip", "0004_auto_20150916_1934"),
        ("afip", "0005_auto_20150918_0115"),
        ("afip", "0006_auto_20151212_1431"),
        ("afip", "0007_auto_20151212_1754"),
        ("afip", "0008_auto_20151212_1820"),
        ("afip", "0009_auto_20151214_1836"),
        ("afip", "0010_receiptpdf_pdffile_uploadto"),
        ("afip", "0011_receipt_entry_vat"),
        ("afip", "0012_taxpayer_profile_one_to_one"),
        ("afip", "0013_taxpayer_is_sandboxed"),
        ("afip", "0014_no_partially_validated_receiptvalidations"),
        ("afip", "0015_receiptentry__amount_to_quantity"),
        ("afip", "0016_auto_20170529_2012"),
        ("afip", "0017_receipt_issued_date"),
        ("afip", "0018_on_delete_fks"),
        ("afip", "0019_receiptvalidation__processed_date"),
        ("afip", "0020_backfill_receiptvalidation__processed_date"),
        ("afip", "0021_drop_batches"),
        ("afip", "0022_auto_misc_tweaks"),
        ("afip", "0023_taxpayer__certs_blank"),
        ("afip", "0024_taxpayer__certificate_expiration"),
        ("afip", "0025_receipt__default_currency"),
        ("afip", "0026_vat_conditions"),
        ("afip", "0027_taxpayer__active_since"),
        ("afip", "0028_taxpayer__copy_active_since"),
        ("afip", "0029_drop__taxpayerprofile__active_since"),
        ("afip", "0030_receiptpdf_client_vat_condition"),
        ("afip", "0031_receiptpdf__copy_vat_condition"),
        ("afip", "0032_receiptpdf__client_vat__notnull"),
        ("afip", "0033_receiptpdf__pdf_file__help_text"),
        ("afip", "0034_vat_condition_choices"),
        ("afip", "0035_receiptentry__vat__blankable"),
        ("afip", "0036_receiptpdf__client_address__blank"),
    ]

    initial = True

    dependencies: List[str] = []

    operations = [
        migrations.CreateModel(
            name="AuthTicket",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "unique_id",
                    models.IntegerField(
                        default=django_afip.models.AuthTicket.default_unique_id,
                        verbose_name="unique id",
                    ),
                ),
                (
                    "generated",
                    models.DateTimeField(
                        default=django_afip.models.AuthTicket.default_generated,
                        verbose_name="generated",
                    ),
                ),
                (
                    "expires",
                    models.DateTimeField(
                        default=django_afip.models.AuthTicket.default_expires,
                        verbose_name="expires",
                    ),
                ),
                (
                    "service",
                    models.CharField(
                        help_text="Service for which this ticket has been authorized",
                        max_length=6,
                        verbose_name="service",
                    ),
                ),
                ("token", models.TextField(verbose_name="token")),
                ("signature", models.TextField(verbose_name="signature")),
            ],
            options={
                "verbose_name": "authorization ticket",
                "verbose_name_plural": "authorization tickets",
            },
        ),
        migrations.CreateModel(
            name="ConceptType",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.CharField(max_length=3, verbose_name="code")),
                (
                    "description",
                    models.CharField(max_length=250, verbose_name="description"),
                ),
                (
                    "valid_from",
                    models.DateField(blank=True, null=True, verbose_name="valid from"),
                ),
                (
                    "valid_to",
                    models.DateField(blank=True, null=True, verbose_name="valid until"),
                ),
            ],
            options={
                "verbose_name": "concept type",
                "verbose_name_plural": "concept types",
            },
        ),
        migrations.CreateModel(
            name="CurrencyType",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.CharField(max_length=3, verbose_name="code")),
                (
                    "description",
                    models.CharField(max_length=250, verbose_name="description"),
                ),
                (
                    "valid_from",
                    models.DateField(blank=True, null=True, verbose_name="valid from"),
                ),
                (
                    "valid_to",
                    models.DateField(blank=True, null=True, verbose_name="valid until"),
                ),
            ],
            options={
                "verbose_name": "currency type",
                "verbose_name_plural": "currency types",
            },
        ),
        migrations.CreateModel(
            name="DocumentType",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.CharField(max_length=3, verbose_name="code")),
                (
                    "description",
                    models.CharField(max_length=250, verbose_name="description"),
                ),
                (
                    "valid_from",
                    models.DateField(blank=True, null=True, verbose_name="valid from"),
                ),
                (
                    "valid_to",
                    models.DateField(blank=True, null=True, verbose_name="valid until"),
                ),
            ],
            options={
                "verbose_name": "document type",
                "verbose_name_plural": "document types",
            },
        ),
        migrations.CreateModel(
            name="Observation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.PositiveSmallIntegerField(verbose_name="code")),
                ("message", models.CharField(max_length=255, verbose_name="message")),
            ],
            options={
                "verbose_name": "observation",
                "verbose_name_plural": "observations",
            },
        ),
        migrations.CreateModel(
            name="PointOfSales",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("number", models.PositiveSmallIntegerField(verbose_name="number")),
                (
                    "issuance_type",
                    models.CharField(
                        help_text="Indicates if thie POS emits using CAE and CAEA.",
                        max_length=8,
                        verbose_name="issuance type",
                    ),
                ),
                ("blocked", models.BooleanField(verbose_name="blocked")),
                (
                    "drop_date",
                    models.DateField(blank=True, null=True, verbose_name="drop date"),
                ),
            ],
            options={
                "verbose_name": "point of sales",
                "verbose_name_plural": "points of sales",
            },
        ),
        migrations.CreateModel(
            name="Receipt",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "document_number",
                    models.BigIntegerField(
                        help_text=(
                            "The document number of the customer to whom this receipt"
                            " is addressed"
                        ),
                        verbose_name="document number",
                    ),
                ),
                (
                    "receipt_number",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text=(
                            "If left blank, the next valid number will assigned when"
                            " validating the receipt."
                        ),
                        null=True,
                        verbose_name="receipt number",
                    ),
                ),
                (
                    "issued_date",
                    models.DateField(
                        help_text=(
                            "Can diverge up to 5 days for good, or 10 days otherwise"
                        ),
                        verbose_name="issued date",
                    ),
                ),
                (
                    "total_amount",
                    models.DecimalField(
                        decimal_places=2,
                        help_text=(
                            "Must be equal to the sum of net_taxed, exempt_amount,"
                            " net_taxes, and all taxes and vats."
                        ),
                        max_digits=15,
                        verbose_name="total amount",
                    ),
                ),
                (
                    "net_untaxed",
                    models.DecimalField(
                        decimal_places=2,
                        help_text=(
                            "The total amount to which taxes do not apply. For C-type"
                            " receipts, this must be zero."
                        ),
                        max_digits=15,
                        verbose_name="total untaxable amount",
                    ),
                ),
                (
                    "net_taxed",
                    models.DecimalField(
                        decimal_places=2,
                        help_text=(
                            "The total amount to which taxes apply. For C-type"
                            " receipts, this is equal to the subtotal."
                        ),
                        max_digits=15,
                        verbose_name="total taxable amount",
                    ),
                ),
                (
                    "exempt_amount",
                    models.DecimalField(
                        decimal_places=2,
                        help_text=(
                            "Only for categories which are tax-exempt. For C-type"
                            " receipts, this must be zero."
                        ),
                        max_digits=15,
                        verbose_name="exempt amount",
                    ),
                ),
                (
                    "service_start",
                    models.DateField(
                        blank=True,
                        help_text=(
                            "Date on which a service started. No applicable for goods."
                        ),
                        null=True,
                        verbose_name="service start date",
                    ),
                ),
                (
                    "service_end",
                    models.DateField(
                        blank=True,
                        help_text=(
                            "Date on which a service ended. No applicable for goods."
                        ),
                        null=True,
                        verbose_name="service end date",
                    ),
                ),
                (
                    "expiration_date",
                    models.DateField(
                        blank=True,
                        help_text=(
                            "Date on which this receipt expires. No applicable for"
                            " goods."
                        ),
                        null=True,
                        verbose_name="receipt expiration date",
                    ),
                ),
                (
                    "currency_quote",
                    models.DecimalField(
                        decimal_places=6,
                        default=1,
                        help_text=(
                            "Quote of the day for the currency used in the receipt"
                        ),
                        max_digits=10,
                        verbose_name="currency quote",
                    ),
                ),
                (
                    "concept",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="receipts",
                        to="afip.ConceptType",
                        verbose_name="concept",
                    ),
                ),
                (
                    "currency",
                    models.ForeignKey(
                        default=django_afip.models.first_currency,
                        help_text="Currency in which this receipt is issued.",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="documents",
                        to="afip.CurrencyType",
                        verbose_name="currency",
                    ),
                ),
                (
                    "document_type",
                    models.ForeignKey(
                        help_text=(
                            "The document type of the customer to whom this receipt is"
                            " addressed"
                        ),
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="receipts",
                        to="afip.DocumentType",
                        verbose_name="document type",
                    ),
                ),
                (
                    "point_of_sales",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="receipts",
                        to="afip.PointOfSales",
                        verbose_name="point of sales",
                    ),
                ),
            ],
            options={
                "verbose_name": "receipt",
                "verbose_name_plural": "receipts",
                "ordering": ("issued_date",),
            },
        ),
        migrations.CreateModel(
            name="ReceiptEntry",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "description",
                    models.CharField(max_length=128, verbose_name="description"),
                ),
                ("quantity", models.PositiveSmallIntegerField(verbose_name="quantity")),
                (
                    "unit_price",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Price per unit before vat or taxes.",
                        max_digits=15,
                        verbose_name="unit price",
                    ),
                ),
                (
                    "receipt",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="entries",
                        to="afip.Receipt",
                        verbose_name="receipt",
                    ),
                ),
            ],
            options={
                "verbose_name": "receipt entry",
                "verbose_name_plural": "receipt entries",
            },
        ),
        migrations.CreateModel(
            name="ReceiptPDF",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "pdf_file",
                    models.FileField(
                        blank=True,
                        help_text="The actual file which contains the PDF data.",
                        null=True,
                        upload_to="receipts",
                        verbose_name="pdf file",
                    ),
                ),
                (
                    "issuing_name",
                    models.CharField(max_length=128, verbose_name="issuing name"),
                ),
                ("issuing_address", models.TextField(verbose_name="issuing address")),
                (
                    "issuing_email",
                    models.CharField(
                        blank=True,
                        max_length=128,
                        null=True,
                        verbose_name="issuing email",
                    ),
                ),
                (
                    "vat_condition",
                    models.CharField(
                        choices=[
                            ("IVA Responsable Inscripto", "IVA Responsable Inscripto"),
                            (
                                "IVA Responsable No Inscripto",
                                "IVA Responsable No Inscripto",
                            ),
                            ("IVA Exento", "IVA Exento"),
                            ("No Responsable IVA", "No Responsable IVA"),
                            ("Responsable Monotributo", "Responsable Monotributo"),
                        ],
                        max_length=48,
                        verbose_name="vat condition",
                    ),
                ),
                (
                    "gross_income_condition",
                    models.CharField(
                        max_length=48, verbose_name="gross income condition"
                    ),
                ),
                (
                    "client_name",
                    models.CharField(max_length=128, verbose_name="client name"),
                ),
                (
                    "client_address",
                    models.TextField(blank=True, verbose_name="client address"),
                ),
                (
                    "client_vat_condition",
                    models.CharField(
                        choices=[
                            ("IVA Responsable Inscripto", "IVA Responsable Inscripto"),
                            (
                                "IVA Responsable No Inscripto",
                                "IVA Responsable No Inscripto",
                            ),
                            ("IVA Sujeto Exento", "IVA Sujeto Exento"),
                            ("Consumidor Final", "Consumidor Final"),
                            ("Responsable Monotributo", "Responsable Monotributo"),
                            ("Proveedor del Exterior", "Proveedor del Exterior"),
                            ("Cliente del Exterior", "Cliente del Exterior"),
                            (
                                "IVA Liberado - Ley Nº 19.640",
                                "IVA Liberado - Ley Nº 19.640",
                            ),
                            (
                                "IVA Responsable Inscripto - Agente de Percepción",
                                "IVA Responsable Inscripto - Agente de Percepción",
                            ),
                            ("Monotributista Social", "Monotributista Social"),
                            ("IVA no alcanzado", "IVA no alcanzado"),
                        ],
                        max_length=48,
                        verbose_name="client vat condition",
                    ),
                ),
                (
                    "sales_terms",
                    models.CharField(
                        help_text=(
                            'Should be something like "Cash", "Payable in 30 days", etc'
                        ),
                        max_length=48,
                        verbose_name="sales terms",
                    ),
                ),
                (
                    "receipt",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="afip.Receipt",
                        verbose_name="receipt",
                    ),
                ),
            ],
            options={
                "verbose_name": "receipt pdf",
                "verbose_name_plural": "receipt pdfs",
            },
        ),
        migrations.CreateModel(
            name="ReceiptType",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.CharField(max_length=3, verbose_name="code")),
                (
                    "description",
                    models.CharField(max_length=250, verbose_name="description"),
                ),
                (
                    "valid_from",
                    models.DateField(blank=True, null=True, verbose_name="valid from"),
                ),
                (
                    "valid_to",
                    models.DateField(blank=True, null=True, verbose_name="valid until"),
                ),
            ],
            options={
                "verbose_name": "receipt type",
                "verbose_name_plural": "receipt types",
            },
        ),
        migrations.CreateModel(
            name="ReceiptValidation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "result",
                    models.CharField(
                        choices=[("A", "approved"), ("R", "rejected")],
                        help_text=(
                            "Indicates whether the validation was succesful or not"
                        ),
                        max_length=1,
                        verbose_name="result",
                    ),
                ),
                ("processed_date", models.DateTimeField(verbose_name="processed date")),
                (
                    "cae",
                    models.CharField(
                        help_text="The CAE as returned by the AFIP",
                        max_length=14,
                        verbose_name="cae",
                    ),
                ),
                (
                    "cae_expiration",
                    models.DateField(
                        help_text="The CAE expiration as returned by the AFIP",
                        verbose_name="cae expiration",
                    ),
                ),
                (
                    "observations",
                    models.ManyToManyField(
                        help_text=(
                            "The observations as returned by the AFIP. These are"
                            " generally present for failed validations."
                        ),
                        related_name="validations",
                        to="afip.Observation",
                        verbose_name="observations",
                    ),
                ),
                (
                    "receipt",
                    models.OneToOneField(
                        help_text="The Receipt for which this validation applies",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="validation",
                        to="afip.Receipt",
                        verbose_name="receipt",
                    ),
                ),
            ],
            options={
                "verbose_name": "receipt validation",
                "verbose_name_plural": "receipt validations",
            },
        ),
        migrations.CreateModel(
            name="Tax",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "description",
                    models.CharField(max_length=80, verbose_name="description"),
                ),
                (
                    "base_amount",
                    models.DecimalField(
                        decimal_places=2, max_digits=15, verbose_name="base amount"
                    ),
                ),
                (
                    "aliquot",
                    models.DecimalField(
                        decimal_places=2, max_digits=5, verbose_name="aliquot"
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2, max_digits=15, verbose_name="amount"
                    ),
                ),
                (
                    "receipt",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="taxes",
                        to="afip.Receipt",
                    ),
                ),
            ],
            options={"verbose_name": "tax", "verbose_name_plural": "taxes"},
        ),
        migrations.CreateModel(
            name="TaxPayer",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="A friendly name to recognize this taxpayer.",
                        max_length=32,
                        verbose_name="name",
                    ),
                ),
                (
                    "key",
                    models.FileField(
                        blank=True, null=True, upload_to="", verbose_name="key"
                    ),
                ),
                (
                    "certificate",
                    models.FileField(
                        blank=True, null=True, upload_to="", verbose_name="certificate"
                    ),
                ),
                ("cuit", models.BigIntegerField(verbose_name="cuit")),
                (
                    "is_sandboxed",
                    models.BooleanField(
                        help_text=(
                            "Indicates if this taxpayer interacts with the sandbox"
                            " servers rather than the production servers"
                        ),
                        verbose_name="is sandboxed",
                    ),
                ),
                (
                    "certificate_expiration",
                    models.DateTimeField(
                        editable=False,
                        help_text=(
                            "Stores expiration for the current certificate. Note that"
                            " this field is updated pre-save, so the value may be"
                            " invalid for unsaved models."
                        ),
                        null=True,
                        verbose_name="certificate expiration",
                    ),
                ),
                (
                    "active_since",
                    models.DateField(
                        help_text=(
                            "Date since which this taxpayer has been legally active."
                        ),
                        verbose_name="active since",
                    ),
                ),
            ],
            options={"verbose_name": "taxpayer", "verbose_name_plural": "taxpayers"},
        ),
        migrations.CreateModel(
            name="TaxPayerProfile",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "issuing_name",
                    models.CharField(max_length=128, verbose_name="issuing name"),
                ),
                ("issuing_address", models.TextField(verbose_name="issuing address")),
                (
                    "issuing_email",
                    models.CharField(
                        blank=True,
                        max_length=128,
                        null=True,
                        verbose_name="issuing email",
                    ),
                ),
                (
                    "vat_condition",
                    models.CharField(
                        choices=[
                            ("IVA Responsable Inscripto", "IVA Responsable Inscripto"),
                            (
                                "IVA Responsable No Inscripto",
                                "IVA Responsable No Inscripto",
                            ),
                            ("IVA Exento", "IVA Exento"),
                            ("No Responsable IVA", "No Responsable IVA"),
                            ("Responsable Monotributo", "Responsable Monotributo"),
                        ],
                        max_length=48,
                        verbose_name="vat condition",
                    ),
                ),
                (
                    "gross_income_condition",
                    models.CharField(
                        max_length=48, verbose_name="gross income condition"
                    ),
                ),
                (
                    "sales_terms",
                    models.CharField(
                        help_text=(
                            "The terms of the sale printed onto receipts by default"
                            " (eg: single payment, checking account, etc)."
                        ),
                        max_length=48,
                        verbose_name="sales terms",
                    ),
                ),
                (
                    "taxpayer",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to="afip.TaxPayer",
                        verbose_name="taxpayer",
                    ),
                ),
            ],
            options={
                "verbose_name": "taxpayer profile",
                "verbose_name_plural": "taxpayer profiles",
            },
        ),
        migrations.CreateModel(
            name="TaxType",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.CharField(max_length=3, verbose_name="code")),
                (
                    "description",
                    models.CharField(max_length=250, verbose_name="description"),
                ),
                (
                    "valid_from",
                    models.DateField(blank=True, null=True, verbose_name="valid from"),
                ),
                (
                    "valid_to",
                    models.DateField(blank=True, null=True, verbose_name="valid until"),
                ),
            ],
            options={"verbose_name": "tax type", "verbose_name_plural": "tax types"},
        ),
        migrations.CreateModel(
            name="Vat",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "base_amount",
                    models.DecimalField(
                        decimal_places=2, max_digits=15, verbose_name="base amount"
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2, max_digits=15, verbose_name="amount"
                    ),
                ),
                (
                    "receipt",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="vat",
                        to="afip.Receipt",
                    ),
                ),
            ],
            options={"verbose_name": "vat", "verbose_name_plural": "vat"},
        ),
        migrations.CreateModel(
            name="VatType",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.CharField(max_length=3, verbose_name="code")),
                (
                    "description",
                    models.CharField(max_length=250, verbose_name="description"),
                ),
                (
                    "valid_from",
                    models.DateField(blank=True, null=True, verbose_name="valid from"),
                ),
                (
                    "valid_to",
                    models.DateField(blank=True, null=True, verbose_name="valid until"),
                ),
            ],
            options={"verbose_name": "vat type", "verbose_name_plural": "vat types"},
        ),
        migrations.AddField(
            model_name="vat",
            name="vat_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="afip.VatType",
                verbose_name="vat type",
            ),
        ),
        migrations.AddField(
            model_name="tax",
            name="tax_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="afip.TaxType",
                verbose_name="tax type",
            ),
        ),
        migrations.AddField(
            model_name="receiptentry",
            name="vat",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="receipt_entries",
                to="afip.VatType",
                verbose_name="vat",
            ),
        ),
        migrations.AddField(
            model_name="receipt",
            name="receipt_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="receipts",
                to="afip.ReceiptType",
                verbose_name="receipt type",
            ),
        ),
        migrations.AddField(
            model_name="receipt",
            name="related_receipts",
            field=models.ManyToManyField(
                blank=True, to="afip.Receipt", verbose_name="related receipts"
            ),
        ),
        migrations.AddField(
            model_name="pointofsales",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="points_of_sales",
                to="afip.TaxPayer",
                verbose_name="owner",
            ),
        ),
        migrations.AddField(
            model_name="authticket",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="auth_tickets",
                to="afip.TaxPayer",
                verbose_name="owner",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="receipt",
            unique_together={("point_of_sales", "receipt_type", "receipt_number")},
        ),
        migrations.AlterUniqueTogether(
            name="pointofsales",
            unique_together={("number", "owner")},
        ),
    ]
