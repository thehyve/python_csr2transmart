from typing import Sequence, Type, Dict, Any, List

from pydantic import BaseModel


def validate_entity_data(entity_data: Dict[str, Sequence[Any]], allowed_entity_types: List[Type[BaseModel]]):
    for entity_type_name, entities in entity_data.items():
        entity_types = [entity_type for entity_type in allowed_entity_types
                        if entity_type.schema()['title'] == entity_type_name]
        if not entity_types:
            raise Exception(f'Invalid entity type in subject registry: {entity_type_name}.')
        entity_type = entity_types[0]
        for entity in entities:
            if type(entity) is not entity_type:
                raise Exception(f'Found entity of type {type(entity)}, but expected {entity_type_name}: {entity}')
