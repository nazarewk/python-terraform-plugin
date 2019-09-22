import enum

from .. import tfplugin51_pb2_grpc


class Type(enum.IntEnum):
    """From Terraform sources"""
    Invalid = enum.auto()
    Bool = enum.auto()
    Int = enum.auto()
    Float = enum.auto()
    String = enum.auto()
    List = enum.auto()
    Map = enum.auto()
    Set = enum.auto()
    Object = enum.auto()


class ProviderBase(tfplugin51_pb2_grpc.ProviderServicer):
    pass
