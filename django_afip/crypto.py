from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.serialization.pkcs7 import PKCS7Options
from cryptography.hazmat.primitives.serialization.pkcs7 import PKCS7SignatureBuilder
from cryptography.x509 import load_pem_x509_certificate
from OpenSSL import crypto

from django_afip import exceptions


def create_embeded_pkcs7_signature(data: bytes, cert: bytes, key: bytes):
    """Creates an embedded ("nodetached") PKCS7 signature.

    This is equivalent to the output of::

        openssl smime -sign -signer cert -inkey key -outform DER -nodetach < data
    """

    try:
        pkey = load_pem_private_key(key, None)
        signcert = load_pem_x509_certificate(cert)
    except Exception as e:
        raise exceptions.CorruptCertificate from e

    signed_data = (
        PKCS7SignatureBuilder()
        .set_data(data)
        .add_signer(signcert, pkey, hashes.SHA256())
        .sign(Encoding.DER, [PKCS7Options.Binary])
    )
    return signed_data


def create_key(file_):
    """
    Create a key and save it into ``file_``.

    Note that ``file`` must be opened in binary mode.
    """
    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_RSA, 2048)

    file_.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))
    file_.flush()


def create_csr(key_file, organization_name, common_name, serial_number, file_):
    """Create a CSR for a key, and save it into ``file_``."""
    key = crypto.load_privatekey(crypto.FILETYPE_PEM, key_file.read())

    req = crypto.X509Req()
    subj = req.get_subject()

    subj.O = organization_name  # noqa: E741 (we can't do anything about this)
    subj.CN = common_name
    subj.serialNumber = serial_number

    req.set_pubkey(key)
    req.sign(key, "md5")

    file_.write(crypto.dump_certificate_request(crypto.FILETYPE_PEM, req))
