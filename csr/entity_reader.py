import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Type
from pydantic import BaseModel
from csr.tabular_file_reader import TabularFileReader

logger = logging.getLogger(__name__)


class EntityReader:
    """Reader that reads entity data from tab delimited files.
    """
    def __init__(self, input_dir: str):
        self.input_dir = input_dir

    @staticmethod
    def get_date_fields(schema: Dict[str, Any]) -> List[str]:
        date_fields: List[str] = []
        for name, field in schema['properties'].items():
            if field.get('format') == 'date':
                date_fields.append(name)
        return date_fields

    @staticmethod
    def get_array_fields(schema: Dict[str, Any]) -> List[str]:
        return [name
                for name, field in schema['properties'].items()
                if field.get('type') == 'array']

    def read_entities(self, file_path: str, entity_type: Type[BaseModel]) -> List[Any]:
        try:
            data = TabularFileReader(file_path).read_data()
        except FileNotFoundError:
            return []

        date_fields = self.get_date_fields(entity_type.schema())
        array_fields = self.get_array_fields(entity_type.schema())

        for row in data:
            for field, value in row.items():
                if value == '' or value == 'NA':
                    row[field] = None
                elif field in date_fields:
                    row[field] = datetime.strptime(value, '%Y-%m-%d')
                elif field in array_fields:
                    row[field] = json.loads(value)
        return [entity_type(**d) for d in list(data)]
