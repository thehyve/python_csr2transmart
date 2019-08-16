import logging
from typing import List, Dict, Any

import pandas as pd

logger = logging.getLogger(__name__)


class EntityReader:
    """Reader that reads entity data from tab delimited files.
    """
    def __init__(self, input_dir: str):
        self.input_dir = input_dir

    @staticmethod
    def get_date_fields(schema: Dict) -> List[str]:
        date_fields: List[str] = []
        for field in schema['properties'].values():
            if field.get('format') == 'date':
                date_fields.append(field['title'].lower())
        return date_fields

    def read_entities(self, file_name: str, schema: Dict) -> List[Dict[str, Any]]:
        values_df = pd.read_csv(file_name, sep='\t', parse_dates=True)
        values_df.columns = map(str.lower, values_df.columns)

        for date_field in self.get_date_fields(schema):
            if date_field in values_df:
                try:
                    values_df[date_field] = pd.to_datetime(values_df[date_field], format='%d-%m-%Y')
                except ValueError:
                    values_df[date_field] = pd.to_datetime(values_df[date_field])
        values_df.replace({pd.np.nan: None}, inplace=True)

        return values_df.to_dict('records')


