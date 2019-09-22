import base64
import logging
import os
import random
import sys
import time
from concurrent import futures

import grpc

from terraform_provider import tfplugin51_pb2_grpc
from terraform_provider.plugin.constants import (
    CoreProtocolVersion,
    DefaultProtocolVersion,
    get_protocol_version,
    ONE_DAY_IN_SECONDS,
    PluginCertKey,
    PluginProtocolVersionKey,
)
from terraform_provider.plugin.crypto import get_server_credentials
from terraform_provider.provider import ProviderBase
from . import constants

log = logging.getLogger(__name__)


# https://github.com/hashicorp/terraform/blob/7816e61614095355c140344f048bb8c323a04066/plugin/serve.go

def serve(provider: ProviderBase):
    proto_type = 'grpc'
    port = random.randint(49152, 61000)
    listener_addr_network = 'tcp'
    listener_addr_string = f'127.0.0.1:{port}'

    server_credentials, server_certificate_bytes = get_server_credentials()
    certificate = base64.b64encode(server_certificate_bytes).decode('utf8')
    log.info(f'Client Certificate: {os.getenv(constants.PluginCertKey)!r}')
    log.info(f'Server Certificate: {certificate}')
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
            time.sleep(ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)
