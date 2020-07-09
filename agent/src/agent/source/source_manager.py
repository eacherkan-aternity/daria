import jsonschema

from .abstract_source import Source
from .monitoring import MonitoringSource
from agent.constants import MONITORING_SOURCE_NAME
from agent.repository import source_repository
from agent import source


def create_object(name: str, source_type: str) -> Source:
    if name == MONITORING_SOURCE_NAME:
        return MonitoringSource(MONITORING_SOURCE_NAME, source.TYPE_MONITORING, {})

    if source_type not in source.types:
        raise ValueError(f'{source_type} isn\'t supported')
    return source.types[source_type](name, source_type, {})


def create_from_json(config: dict) -> Source:
    source_instance = create_object(config['name'], config['type'])
    source_instance.set_config(config['config'])
    source_instance.validate()
    source_repository.create(source_instance)
    return source_instance


def edit_using_json(config: dict) -> Source:
    source_instance = source_repository.get(config['name'])
    source_instance.set_config(config['config'])
    source_instance.validate()
    source_repository.update(source_instance)
    return source_instance


def validate_json_for_create(json: dict):
    schema = {
        'type': 'array',
        'items': source.json_schema
    }
    jsonschema.validate(json, schema)


def validate_json_for_edit(json: dict):
    schema = {
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': {
                'name': {'type': 'string', 'minLength': 1, 'maxLength': 100, 'enum': source_repository.get_all()},
                'config': {'type': 'object'}
            },
            'required': ['name', 'config']
        }
    }
    jsonschema.validate(json, schema)