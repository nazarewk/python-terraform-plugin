import datetime
import os

import grpc
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKeyWithSerialization
from cryptography.x509 import Certificate, load_der_x509_certificate

from terraform_provider.plugin.constants import PluginCertKey


def utcnow():
    return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)


def generate_private_key():
    key: EllipticCurvePrivateKeyWithSerialization = ec.generate_private_key(
        ec.SECP521R1, default_backend()
    )
    key_bytes: bytes = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return key, key_bytes


def generate_certificate(key: EllipticCurvePrivateKeyWithSerialization):
    hostname = 'localhost'
    subject = issuer = x509.Name([
        x509.NameAttribute(x509.NameOID.COMMON_NAME, hostname)
    ])

    cert: Certificate = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        utcnow() - datetime.timedelta(seconds=60)
    ).not_valid_after(
        utcnow() + datetime.timedelta(days=1)
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=None),
        critical=True
    ).add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=False,
            key_encipherment=True,
            data_encipherment=False,
            key_agreement=True,
            key_cert_sign=True,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    ).add_extension(
        x509.ExtendedKeyUsage([
            x509.ExtendedKeyUsageOID.SERVER_AUTH,
            x509.ExtendedKeyUsageOID.CLIENT_AUTH,
        ]),
        critical=False
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName(hostname),
        ]),
        critical=False
    ).sign(key, hashes.SHA256(), default_backend())

    return cert


def read_certificate(der_data: bytes) -> Certificate:
    return load_der_x509_certificate(der_data, backend=default_backend())


def get_server_credentials():
    """
    https://www.sandtable.com/using-ssl-with-grpc-in-python/
    :return:
    """
    client_cert_pem = os.getenv(PluginCertKey)

    private_key, private_key_bytes = generate_private_key()
    certificate = generate_certificate(private_key)

    certificate_chain_bytes: bytes = b'\n'.join((
        certificate.public_bytes(serialization.Encoding.DER),
    ))
    credentials: grpc.ServerCredentials = grpc.ssl_server_credentials(
        private_key_certificate_chain_pairs=(
            (
                private_key_bytes,
                certificate.public_bytes(serialization.Encoding.PEM),
            ),
        ),
    )

    return credentials, certificate_chain_bytes
