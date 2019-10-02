import enum
from typing import Any

from grpc._server import _Server

from terraform_plugin.proto.tfplugin51_pb2 import (
    Configure,
    PrepareProviderConfig,
    Stop,
    ValidateDataSourceConfig,
    ValidateResourceTypeConfig,
)
from ..proto import tfplugin51_pb2_grpc


class Type(enum.IntEnum):
    """
    https://github.com/hashicorp/terraform/blob/fa7f496bef9da0b49728b969ac1b597b73d92c83/helper/schema/valuetype.go#L8-L18
    """
    Invalid = enum.auto()
    Bool = enum.auto()
    Int = enum.auto()
    Float = enum.auto()
    String = enum.auto()
    List = enum.auto()
    Map = enum.auto()
    Set = enum.auto()
    _Object = enum.auto()


class PrimitiveType(enum.Enum):
    """
    https://github.com/hashicorp/terraform/blob/aa6b55bb17955d73c24fd828c89d0a5ab19c13ff/vendor/github.com/zclconf/go-cty/cty/primitive_type.go#L14-L18
    """
    Bool = b'B'
    Number = b'N'
    String = b'S'


class ProviderBase(tfplugin51_pb2_grpc.ProviderServicer):
    def __init__(self, server: _Server = None):
        self.server = server

    def bind(self, server: _Server = None):
        self.server = server

    def Configure(
            self,
            request: Configure.Request,
            context: Any
    ) -> Configure.Response:
        return Configure.Response()

    def PrepareProviderConfig(
            self,
            request: PrepareProviderConfig.Request,
            context: Any
    ) -> PrepareProviderConfig.Response:
        return PrepareProviderConfig.Response()

    def ValidateDataSourceConfig(self, request: ValidateDataSourceConfig.Request,
                                 context: Any) -> ValidateDataSourceConfig.Response:
        return ValidateDataSourceConfig.Response()

    def ValidateResourceTypeConfig(self, request: ValidateResourceTypeConfig.Request,
                                   context: Any) -> ValidateResourceTypeConfig.Response:
        return ValidateResourceTypeConfig.Response()

    def Stop(self, request: Stop.Request, context: Any) -> Stop.Response:
        if self.server:
            self.server.stop(0)
        return super().Stop(request, context)
