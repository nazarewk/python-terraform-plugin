import base64
import subprocess
from pathlib import Path

import grpc
from cryptography.hazmat.primitives import serialization

from terraform_plugin.proto.tfplugin51_pb2 import GetProviderSchema
from terraform_plugin.proto.tfplugin51_pb2_grpc import ProviderStub
from terraform_plugin import constants, crypto


def start_plugin(path: Path, secure=False):
    """
    SSL fails due to https://github.com/grpc/grpc/issues/6722
    """
    env = {
        constants.MagicCookieKey: constants.MagicCookieValue,
        constants.PluginProtocolVersionKey: str(constants.DefaultProtocolVersion),
    }

    if secure:
        private_key, private_key_bytes = crypto.generate_private_key()
        certificate = crypto.generate_certificate(private_key)
        certificate_bytes: bytes = certificate.public_bytes(serialization.Encoding.PEM)
        env[constants.PluginCertKey] = certificate_bytes.decode()

    path_str = str(path.absolute())
    process = subprocess.Popen([
        path_str,
        path_str,
    ], env=env, stdout=subprocess.PIPE)

    line_bytes: bytes = process.stdout.readline()
    line: str = line_bytes.decode()
    (
        core_plugin_version,
        protocol_version,
        network_type,
        network_address,
        protocol_type,
        *remainder,
    ) = line.strip().split('|')

    assert int(protocol_version) == constants.DefaultProtocolVersion
    assert protocol_type == 'grpc'
    channel_address = f'{network_type}:{network_address}'

    if secure:
        server_certificate_base64, *_ = remainder
        # add missing padding
        server_certificate_base64 += '=' * (len(server_certificate_base64) % 4)

        server_certificate_der_bytes = base64.b64decode(server_certificate_base64)

        server_certificate = crypto.read_certificate(server_certificate_der_bytes)

        server_certificate_pem_bytes = server_certificate.public_bytes(serialization.Encoding.PEM)
        credentials = grpc.ssl_channel_credentials(
            root_certificates=server_certificate_pem_bytes,
            private_key=private_key_bytes,
            certificate_chain=certificate_bytes,
        )
        channel = grpc.secure_channel(channel_address, credentials=credentials)
    else:
        channel = grpc.insecure_channel(channel_address)

    stub = ProviderStub(channel=channel)
    return process, stub


def _main():
    import sys
    proc, stub = start_plugin(Path(
        sys.argv[1]
    ))

    print(repr(stub.GetSchema(GetProviderSchema.Request())))


if __name__ == '__main__':
    _main()
