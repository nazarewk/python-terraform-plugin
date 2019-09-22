import logging
from typing import Any

from terraform_provider import plugin
from terraform_provider.tfplugin51_pb2 import GetProviderSchema, Schema

log = logging.getLogger(__name__)


class ExampleProvider(plugin.ProviderBase):
    def GetSchema(self, request: GetProviderSchema.Request, context: Any) -> GetProviderSchema.Response:
        log.info(f'{self.__class__.__name__}.GetSchema(request={request!r}, context={context!r})')
        response = GetProviderSchema.Response(
            provider=Schema(
                block=Schema.Block(
                    attributes=[
                    ]
                ),
            ),
            resource_schemas={
                'example_example': Schema(
                    block=Schema.Block(
                        attributes=[]
                    )
                )
            }
        )
        log.info(f'Returning: {response!r}')
        return response
