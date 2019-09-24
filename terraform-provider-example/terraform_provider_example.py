import json
import logging
import sys
from typing import Any

import msgpack

from terraform_provider import provider
from terraform_provider.plugin import server
from terraform_provider.tfplugin51_pb2 import GetProviderSchema, Schema, ReadDataSource, DynamicValue, \
    ValidateDataSourceConfig

log = logging.getLogger(__name__)


class ExampleProvider(provider.ProviderBase):
    """
    Test schema types defined in https://www.terraform.io/docs/extend/schemas/schema-types.html
    Test nested schema types defined in https://github.com/hashicorp/terraform/blob/88e76fa9ef219d28bd626da2756ebb483daa8756/configs/configschema/schema.go#L82-L130
    """

    def GetSchema(self, request: GetProviderSchema.Request, context: Any) -> GetProviderSchema.Response:
        log.debug(f'{self.__class__.__name__}.GetSchema(request={request!r}, context={context!r})')
        computed_string = [
            Schema.Attribute(
                name='computed_string',
                type=b'"string"',
                computed=True,
            )
        ]
        computed_attributes = [
            *computed_string,
            Schema.Attribute(
                name='computed_int',
                type=b'"number"',
                computed=True,
            ),
            Schema.Attribute(
                name='computed_float',
                type=b'"number"',
                computed=True,
            ),
            Schema.Attribute(
                name='computed_true',
                type=b'"bool"',
                computed=True,
            ),
            Schema.Attribute(
                name='computed_false',
                type=b'"bool"',
                computed=True,
            ),
            Schema.Attribute(
                name='computed_map',
                type=json.dumps(["map", "string"]).encode(),
                computed=True,
            ),
            Schema.Attribute(
                name='computed_list',
                type=json.dumps(["list", "string"]).encode(),
                computed=True,
            ),
            Schema.Attribute(
                name='computed_set',
                type=json.dumps(["set", "string"]).encode(),
                computed=True,
            ),
        ]
        response = GetProviderSchema.Response(
            provider=Schema(
                block=Schema.Block(
                    attributes=[
                    ]
                ),
            ),
            data_source_schemas={
                'example_example': Schema(
                    block=Schema.Block(
                        attributes=computed_attributes,
                        block_types=[
                            Schema.NestedBlock(
                                type_name='nested_single',
                                nesting=Schema.NestedBlock.NestingMode.SINGLE,
                                block=Schema.Block(
                                    attributes=computed_string,
                                )
                            ),
                            Schema.NestedBlock(
                                type_name='nested_list',
                                nesting=Schema.NestedBlock.NestingMode.LIST,
                                block=Schema.Block(
                                    attributes=computed_string,
                                )
                            ),
                            Schema.NestedBlock(
                                type_name='nested_set',
                                nesting=Schema.NestedBlock.NestingMode.SET,
                                block=Schema.Block(
                                    attributes=computed_string,
                                )
                            ),
                            Schema.NestedBlock(
                                type_name='nested_map',
                                nesting=Schema.NestedBlock.NestingMode.MAP,
                                block=Schema.Block(
                                    attributes=computed_string,
                                )
                            ),
                            Schema.NestedBlock(
                                type_name='nested_group',
                                nesting=Schema.NestedBlock.NestingMode.GROUP,
                                block=Schema.Block(
                                    attributes=computed_string,
                                )
                            ),
                        ]
                    )
                )
            }
        )
        log.info(f'Returning: {response!r}')
        return response

    def ValidateDataSourceConfig(self, request: ValidateDataSourceConfig.Request,
                                 context: Any) -> ValidateDataSourceConfig.Response:
        return ValidateDataSourceConfig.Response()

    def ReadDataSource(self, request: ReadDataSource.Request, context: Any) -> ReadDataSource.Response:
        computed_string = {
            'computed_string': 'computed_string_value',
        }
        computed_data = {
            **computed_string,
            'computed_int': 123,
            'computed_float': 123.456,
            'computed_true': True,
            'computed_false': False,
            'computed_map': {
                'key': 'value',
            },
            'computed_list': ['val1', 'val2', 'val3'],
            'computed_set': ['entry1', 'entry2', 'entry3'],
        }
        data = {
            **computed_data,
            'nested_single': computed_string,
            'nested_group': computed_string,
            'nested_list': [computed_string],
            'nested_set': [computed_string],
            'nested_map': {
                'key1': computed_string,
            }
        }
        msgpack_bytes = msgpack.packb(data, use_bin_type=True)
        value = DynamicValue(
            msgpack=msgpack_bytes
        )
        response = ReadDataSource.Response(
            state=value
        )
        log.info(f'ReadDataSource -> {response!r}')
        return response


if __name__ == '__main__':
    if '--help' in sys.argv:
        print(repr(sys.argv))
        sys.exit()
    logging.basicConfig(level='INFO')
    server.serve(ExampleProvider())
