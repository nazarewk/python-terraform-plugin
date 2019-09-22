import enum

from .. import tfplugin51_pb2_grpc


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
    pass
