Changelog
=========

This file contains a brief summary of new features and dependency changes or
releases, in reverse chronological order.

9.0.0
-----

* Dropped support for Django 3.0.
* Add support for Django 3.2.

8.0.4
-----

* Fix mixup when sending validated receipts, introduced in v8.0.3.

8.0.3
-----

* Some factories were not fully reusable since they depended on data files that
  were no included in this package. These files are now included, and all
  factories should now be reusable by downstream apps.
* Fixed a bug when validating credit notes and other receipts which have a
  related-receipt.

.. warning::

    This version has a critical error in validating receipts with related
    receipts. It has been yanked and should not be used. If you've submitted
    any receipts with this version, you may need to invalidate them.

8.0.2
-----

* Fix typo in dependency specifier.

8.0.1
-----

* Fix improperly pinned Django version that excluded 3.1.x minor releases.

8.0.0
-----
* Receipts now show validation details in the admin.
* The ``__str__`` for ``TaxPayer`` has changed. If you relied on this for rendering
  content, please updated those references to :attr:`.TaxPayer.cuit`.
* Python 3.6 to 3.9 are supported.
* Django 2.2 to 3.1 are supported.
* The template tag ``receiptnumber`` (which was deprecated in 3.0.0) has been removed.
  Use :attr:`.Receipt.formatted_number` instead.
* Template discovery has been extended. See :meth:`~.ReceiptPDFView.get_template_names`
  for the new behaviour.
  The new behaviour is backwards compatible with pre-8.0.0 and does not require any
  changes.
* ``django_afip.views.ReceiptPDFDownloadView`` has been dropped. It was never
  documented, and not really of great use. If you need to expose PDFs prompting the
  user to download the file, use:

.. code:: python

    class MyPDFReceiptView(ReceiptPDFView):
        """Indicates to browsers that they should prompt to download the file."""
        prompt_download = True

        @property
        def download_name(self):
            # You can customise the filename here.
            # This is the default behaviour:
            return f"{self.receipt.formatted_number}.pdf"

* QR Codes have been implemented and replace barcodes in receipts. If you use
  custom receipt templates, you'll need to update them. The provided template
  should serve as a reference.
* The fields from the ``TaxPayerExtras`` have moved into the ``TaxPayer``
  model. A migration will handle copying data from table to the other for you.
  If you have any references to this model (e.g.: forms for your users, custom
  admins, etc), make sure you update these to point to the ``TaxPayer`` model.
* Fixtures are now included with all necessary metadata (currencies, receipt
  types, etc). This should make bootstrapping new projects and environments
  easier.
* The function ``models.populate_all`` has been removed in favour of
  :func:`~.models.loaddata`. The ``afipmetadata`` management command now runs
  the latter.

7.1.2
-----
* Override the TLS configuration for test servers too (7.1.1 only covered
  production servers).

7.1.1
-----
* Override the TLS configuration for AFIP's servers (and only those). They have
  worsened their security configuration, and it's now seen as insecure by
  default on many environments.

7.1.0
-----
* Dropped support for Python < 3.6.
* Dropped support for Django < 2.2.
* Add support for Django 3.0.
* Properly include factoryboy factories so that apps can reuse them.
* Fix some issues with migrations when using external storages.

7.0.0
-----
* Fix crash when retrieving points of sales and their ``issuance_type`` has
  changed.
* Sort receipt pdfs into buckets, to avoid clogging up a single
  directory.
* Fix crash when generating PDFs and the logo is stored in a non-filesystem
  storage.
* Dropped support for Django < 2.0

6.0.1
-----

* Store files in tidier directories. All files handled by the app will be in an
  ``afip`` subdirectory inside ``MEDIA_ROOT``. This does not require any
  changes or updates; existing files will remain in their current location and
  continue to be perfectly usable.
* Added settings to configure storages for different files we handle. See the
  documentation for details on these new settings.

6.0.0
-----

* Add support for Python 3.7.
* Add support for Django 2.1 and Django 2.2
* Dropped support for Django 2.0.
* Dropped support for Python 3.4.
* Fix deserialization bug for AFIP metadata models.
* Include factories for third party usage. These are useful for third party
  apps to reuse for their own tests.

5.0.3
-----

* Fix ocasional bug rendering barcodes.
* Officially support Django 2.0.
* Fix some tests, and drop GitLab CI.

5.0.2
-----
* Moved project to GitHub (this release just updates the docs and links).

5.0.1
-----
* Add templates for B and C type credit notes

5.0.0
-----
* PDF rendering now relies on ``django_renderpdf``, rather than in-tree code,
  and PDF views now subclass that package's ``PDFView``, meaning that all their
  functionality is also available. This results in several changes:

  * ``ReceiptHTMLView`` has been dropped. To force a view to render as an HTML,
    add the querystring ``html=true``. If you want to disable this behaviour
    for your subclasses, add the ``allow_force_html = False`` attribute to your
    subclass.
  * ``ReceiptPDFView`` now makes browsers render the file by default, rather
    than prompting to download a file.
  * ``ReceiptPDFDisplayView`` has been dropped in favour of the above.
  * ``ReceiptPDFDownloadView`` prompts users to download a receipt's PDF. The
    PDF's file name is now customizable by overriding ``get_download_name``.
* Allow filtering receipts [in the admin] by type.
* Allow filtering receipts [in the admin] by issued date.
* Allow searching for currencies by code, as well as name.
* Drop support for Django 1.10.

4.1.7
-----
* Replace pybarcode with python-barcode, which is a fork of the former
  currently being maintained (we no longer depend on --pre releases).

4.1.6
-----
* Fix failing tests due to refactor introduced in 4.1.5.

4.1.5
-----
* The Receipt admin now includes links to each Receipt's PDF.
* Enable editing ``related_receipts`` as auto-complete fields (Django >= 2.0
  only).

4.1.4
-----
* Fix stylesheets for PDFs failing to load on non-filesystem storages.

4.1.3
-----
* Fix issues reading keys and certificates from non-filesystem storages.

4.1.2
-----
* Fix some issues rendering PDFs when not using the default static files app.

4.1.1
-----
* Fix service dates (``None``) being shown for product-only receipts.

4.1.0
-----
* All migrations have been squashed. Please upgrade to 4.0.0 before upgrading
  further. See the docs for details.
* Support for adding custom logos to printable receipts has been added. See the
  new ``TaxPayerExtras`` class for details.

4.0.0
-----
* The ``ReceiptPDF.save_pdf_to`` method has been removed.
* The ``active_since`` field has been moved from ``TaxPayerProfile`` to
  ``TaxPayer``.
* Invoices in the admin will show a small asterisk if their value in the
  original currency doesn't match their value in ARS.
* The ``ReceiptPDF`` class now has a new ``client_vat_condition`` field. Newly
  created instances must define this non-nullable field.
* ``ReceiptPDF`` instances will now auto-generate the PDF file when they are
  saved if the receipt has been validated. Note that they are only generated
  ONCE, and regeneration must be done manually.
* Added a new ``ReceiptPDFDisplayView``, that shows a PDF without prompting
  users to download it.
* Only minimal dependencies are now specified, rather that pinned versions
  (this should avoid silly conflicts with other libraries requiring newer
  versions).
* ``ReceiptEntry.vat`` is now blankable, making forms and admins less
  confusing.
* Remove old monkey-patching code for the ``ssl`` module. This no longer seems
  to be necessary.
* Fix issues displaying static files in receipts when not running in
  development mode.
* ``ReceiptPDF.client_address`` can now be blank, given that this field may be
  absent for certain receipt types.
* Added ``total_vat`` and ``total_tax`` properties to ``Receipt``. This should
  be pretty self-explanatory.

3.3.0
-----
* The ``ReceiptPDF.save_pdf_to`` method has been deprecated and will be removed
  in 4.0.0.
* VAT conditions in models are now limited to know types -- this should very
  much help create UIs and forms. If you come across a missing VAT condition,
  please open an issue for it.
* Improved the documentation surrounding PDF generation.

3.2.1
-----
* Use CAE expirations for receipt barcodes, not receipt expiration. This is the
  behaviour follows by AFIP's own generators, even though the spec doesn't
  explicitly state this.

3.2.0
-----
* New runtime dependency: pyBarcode>=0.8b1.
* The receipt class now has a ``is_validated`` property to check if a single
  instance has been validated.
* All internal errors now raise ``DjangoAfipException`` or a subclass of it.
* Add barcodes to receipt PDFs (AFIP 1702/04).
* TaxPayer certs are now blankable, which should improve admin usability, as
  well as make forms for new TaxPayers friendlier. You might need to check your
  forms if users are expected to always provide a certificate.
* Certificate expiration dates are now stored (via a pre-save hook) and exposed
  by the ``TaxPayer`` model. This should also make it impossible to upload
  garbage instead of a proper certificate file.

3.1.0
-----
* Receipt entries are now shown in the Receipts admin.
* Fix receipt entries being mis-rendered (missing quantity) in PDFs.
* Allow generating PDFs for receipts via the admin.
* Use PES (ARS) as a default currency for Receipts (only if metadata is
  present), and '1' as a currency quote.
* Customized admins are now included for a few more models.

3.0.0
-----
* The entire ``ReceiptBatch`` model has been dropped, along with
  ``Validation``. Receipts are now validated via Receipt querysets, eg:
  ``Receipt.objects.filter(...).validate()``. The existing
  ``ReceiptValidation`` objects remain unchanged.
* Validation of Receipts can now be done in a single action via the ``Receipt``
  admin.
* ``Receipt`` instances have a new ``validate()`` method to validate that
  single receipt.
* The ``receiptnumber`` tag is now deprecated. Use ``Receipt.formatted_number``
  instead.

2.7.0
-----

* Drop support for Django 1.9, support Django 1.11.
* The default ordering of ``Receipt`` instances has now changed, both via
  querysets and in the admin.
* The total amount for receipts is not shown in ARS.
* CI now run tests with all supported Python and Django versions.
* This version has experimental Django 2.0 support.
* Include a new ReceiptPDF admin.
* All exceptions now inherit from ``DjangoAfipException``.

2.6.1
-----

* Language settings of downstream apps should no longer generate bogus
  migrations for ``django-afip``.

2.6.0
-----

* It is now possible to generate keys and CSRs for taxpayers, both
  programmatically, and via the admin.
* The ``AuthTicket.authorize`` method no longer takes a ``save`` argument.
  Authorized tickets are now always immediately saved.
* Add a missing migration.

2.5.1
-----

* Fix an error validating receipts with not VAT or Tax.

2.5.0
-----

* We now rely on ``zeep``, rather ``suds``, update your dependencies
  accordingly.

2.4.0
-----

* Raise ``CertificateExpired``, ``UntrustedCertificate`` or
  ``AuthenticationError`` when attempting an authentication fail.
* The field ``ReceiptEntry.amount`` has been renamed to ``quantity``.
* Add a links to documentation on where to obtain the AFIP WS certificates.
* Introduce this changelog.

2.3.1
-----
* Fix inconsistencies in the return type for ``ReceiptBatch.validate()``.
* Fix bad file names in PDF views.

v2.3.0
------
* Switched from ``suds-py3`` to ``suds-redux``. This should make installation a
  lot easier, since the latter is available on PyPI.

v2.2.1
------
* Fix a crash when fetching more than one point of sale.

v2.2.0
------
* Add support for Django 1.10.
* The ``profile`` parameter has been dropped from the
  ``ReceiptPDF.create_for_receipt`` method.
* Use PyOpenSSL to sign authentication tickets.
* Dropped runtime dependency: The ``openssl`` binary is no longer required.
* Added runtime dependency: ``pyOpenSSL``.

v2.1.2
------
* The package version is not exposed via ``django_afip.__version__``
* Lots of documentation improvements!
* Improve handling of some errors returned by AFIP's WS when using invalid
  credentials.

v2.1.1
------
* Work around PyPI issues which resulted in failed deployments.

v2.1.0
------
* Each ``ReceiptEntry`` can now have a VAT attached to it.
* Add a missing migration.
* Each ``TaxPayer`` instance now has an ``is_sandboxed`` flag. Sandboxes and
  non-sandboxed users can now coexist. This flag should be updated to the
  current value of ``settings.AFIP_DEBUG``. This setting had been dropped and
  will no longer be used.
* Include a management command ``afipmetadata``, to fetch all metadata from
  AFIP's WS.
* Make the ssl monkey-patching as least invasive as possible.
* Improve error handling for ``openssl``  calls.
* Add a new template tag ``format_cuit``, which can be used to format numbers
  as CUITs.

v2.0.3
------
* Save PDF receipts into a ``receipts`` directory inside the media directory.

v2.0.2
------
* Only allow one ``TaxPayerProfile`` per ``TaxPayer``.

v2.0.1
------
* Tidy up exception handling and corner cases for PDF generation.

v2.0.0
------
* Only allow a single ``ReceiptPDF`` instance per ``Receipt``.
* Failed receipt validations no longer raise an exception, but rather return a
  list of errors (since this handles partial validations better).
* Lots of improvements to unit tests and error checking.
