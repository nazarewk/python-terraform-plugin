import json
import logging
import sys
from copy import deepcopy
from typing import Any

import msgpack

from terraform_provider import provider
from terraform_provider.plugin import server
from terraform_provider.tfplugin51_pb2 import GetProviderSchema, Schema, ReadDataSource, DynamicValue, \
    ApplyResourceChange, PlanResourceChange, ReadResource, UpgradeResourceState

log = logging.getLogger(__name__)

data_source_key = 'example_example'
resource_key = 'example_example'


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
            resource_schemas={
                resource_key: Schema(
                    block=Schema.Block(
                        attributes=[
                            Schema.Attribute(
                                name='input',
                                type=b'"string"',
                                required=True,
                            ),
                            Schema.Attribute(
                                name='output',
                                type=b'"string"',
                                computed=True,
                            ),
                        ]
                    )
                ),
            },
            data_source_schemas={
                data_source_key: Schema(
                    block=Schema.Block(
                        attributes=[
                            Schema.Attribute(
                                name='input',
                                type=b'"string"',
                                required=True,
                            ),
                            Schema.Attribute(
                                name='output',
                                type=b'"string"',
                                computed=True,
                            ),
                            *computed_attributes,
                        ],
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
        return response

    def ReadDataSource(self, request: ReadDataSource.Request, context: Any) -> ReadDataSource.Response:
        assert request.type_name == data_source_key
        data = msgpack.loads(request.config.msgpack, encoding='utf-8')
        computed_string = {
            'computed_string': 'computed_string_value',
        }
        data.update({
            'output': data['input'],
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
        })
        data.update({
            'nested_single': computed_string,
            'nested_group': computed_string,
            'nested_list': [computed_string],
            'nested_set': [computed_string],
            'nested_map': {
                'key1': computed_string,
            }
        })
        msgpack_bytes = msgpack.packb(data, use_bin_type=True)
        value = DynamicValue(
            msgpack=msgpack_bytes
        )
        response = ReadDataSource.Response(
            state=value
        )
        return response

    def ReadResource(self, request: ReadResource.Request, context: Any) -> ReadResource.Response:
        assert request.type_name == resource_key
        old_state = msgpack.loads(request.current_state.msgpack, encoding='utf-8') or {}

        new_state = deepcopy(old_state)
        new_state['output'] = 'outputted: ' + new_state.get('input', '<MISSING>')
        return ReadResource.Response(
            new_state=DynamicValue(
                msgpack=msgpack.packb(new_state, use_bin_type=True)
            )
        )

    def PlanResourceChange(self, request: PlanResourceChange.Request, context: Any) -> PlanResourceChange.Response:
        assert request.type_name == resource_key
        old_state = msgpack.loads(request.prior_state.msgpack, encoding='utf-8') or {}
        proposed_state = msgpack.loads(request.proposed_new_state.msgpack, encoding='utf-8') or {}

        new_state = deepcopy(old_state)
        new_state.update(deepcopy(proposed_state))
        new_state['output'] = 'outputted: ' + new_state['input']
        return PlanResourceChange.Response(
            planned_state=DynamicValue(
                msgpack=msgpack.packb(new_state, use_bin_type=True)
            )
        )

    def ApplyResourceChange(self, request: ApplyResourceChange.Request, context: Any) -> ApplyResourceChange.Response:
        assert request.type_name == resource_key

        old_state = msgpack.loads(request.prior_state.msgpack, encoding='utf-8') or {}
        planned_state = msgpack.loads(request.planned_state.msgpack, encoding='utf-8') or {}

        new_state = deepcopy(old_state)
        new_state.update(deepcopy(planned_state))
        new_state['output'] = 'outputted: ' + new_state['input']
        return PlanResourceChange.Response(
            planned_state=DynamicValue(
                msgpack=msgpack.packb(new_state, use_bin_type=True)
            )
        )

    def UpgradeResourceState(self, request: UpgradeResourceState.Request,
                             context: Any) -> UpgradeResourceState.Response:
        assert request.type_name == resource_key

        old_state = json.loads(request.raw_state.json)

        new_state = deepcopy(old_state)

        # # this will trigger permanently changed plan
        # new_state['output'] = 'upgraded: ' + new_state['input']

        return UpgradeResourceState.Response(
            upgraded_state=DynamicValue(
                msgpack=msgpack.packb(new_state, use_bin_type=True)
            )
        )


if __name__ == '__main__':
    if '--help' in sys.argv:
        print(repr(sys.argv))
        sys.exit()
    logging.basicConfig(level='INFO')
    server.serve(ExampleProvider())
