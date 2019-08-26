import logging
from datetime import datetime
from typing import List, Dict, Any, Type
from pydantic import BaseModel
from csr.tsv_reader import TsvReader

logger = logging.getLogger(__name__)


class EntityReader:
    """Reader that reads entity data from tab delimited files.
    """
    def __init__(self, input_dir: str):
        self.input_dir = input_dir

    @staticmethod
    def get_date_fields(schema: Dict[str, Any]) -> List[str]:
        date_fields: List[str] = []
        for field in schema['properties'].values():
            if field.get('format') == 'date':
                date_fields.append(field['title'].lower())
        return date_fields

    def read_entities(self, file_path: str, entity_type: Type[BaseModel]) -> List[Any]:
        try:
            data = TsvReader(file_path).read_data()
        except FileNotFoundError:
            return []

        date_fields = self.get_date_fields(entity_type.schema())

        for row in data:
            for field, value in row.items():
                if value == '' or value == 'NA':
                    row[field] = None
                elif field in date_fields:
                    row[field] = datetime.strptime(value, '%Y-%m-%d')
        return list(data)
