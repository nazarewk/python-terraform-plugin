# https://github.com/hashicorp/go-plugin/blob/4b7600a112d1f7d01c57a72e55275b9f72007030/examples/grpc/plugin-python/plugin.py
import base64
import datetime
import logging
import os
import random
import sys
import time
from concurrent import futures

import grpc
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKeyWithSerialization
from cryptography.x509 import Certificate

from terraform_provider import tfplugin51_pb2_grpc
from terraform_provider.provider import ProviderBase

log = logging.getLogger(__name__)
ProviderPluginName = "provider"
ProvisionerPluginName = "provisioner"
CoreProtocolVersion = 1
DefaultProtocolVersion = 5
MagicCookieKey = "TF_PLUGIN_MAGIC_COOKIE"
MagicCookieValue = "d602bf8f470bc67ca7faa0386276bbdd4330efaf76d1a219cb4d6991ca9872b2"

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


def get_protocol_version():
    versions = sorted(filter(bool, os.getenv('PLUGIN_PROTOCOL_VERSIONS', '').split()), reverse=True)
    for version in versions:
        try:
            int(version)
        except ValueError:
            continue
        return version
    return DefaultProtocolVersion


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


def get_server_credentials():
    """
    https://www.sandtable.com/using-ssl-with-grpc-in-python/
    :return:
    """
    client_cert_pem = os.getenv('PLUGIN_CLIENT_CERT')

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


# https://github.com/hashicorp/terraform/blob/7816e61614095355c140344f048bb8c323a04066/plugin/serve.go

def serve(provider: ProviderBase):
    proto_type = 'grpc'
    port = random.randint(49152, 61000)
    listener_addr_network = 'tcp'
    listener_addr_string = f'127.0.0.1:{port}'

    server_credentials, server_certificate_bytes = get_server_credentials()
    certificate = base64.b64encode(server_certificate_bytes).decode('utf8')
    log.info(f'Certificate: {certificate}')
    certificate = certificate.rstrip('=')

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    tfplugin51_pb2_grpc.add_ProviderServicer_to_server(provider, server)

    if server_credentials:
        server.add_secure_port(listener_addr_string, server_credentials)
    else:
        server.add_secure_port(listener_addr_string)
    server.start()

    # Output information
    print('|'.join(map(str, (
        CoreProtocolVersion,
        get_protocol_version(),
        listener_addr_network,
        listener_addr_string,
        proto_type,
        certificate,
    ))))
    sys.stdout.flush()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)
