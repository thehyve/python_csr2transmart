import json
import logging
import os
from os import path
from typing import Optional, Sequence, Dict, List, Any

from pydantic import BaseModel
from csr.exceptions import FileSystemException
from transmart_loader.tsv_writer import TsvWriter


logger = logging.getLogger(__name__)


class EntityWriter:
    """Writer that writes entity data to tab delimited files.
    """

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        if not path.exists(output_dir):
            logger.info('Creating output directory: {}'.format(output_dir))
            os.makedirs(output_dir, 0o0700, True)

    @staticmethod
    def format_values(values: List[Any]):
        result = []
        for value in values:
            if type(value) is list:
                result.append(json.dumps(value))
            else:
                result.append(value)
        return result

    def write_entities(self, filename: str, schema: Dict, elements: Optional[Sequence[BaseModel]]):
        output_path = self.output_dir + '/' + filename
        if path.exists(output_path):
            raise FileSystemException('File already exists: {}'.format(output_path))
        writer: TsvWriter = TsvWriter(output_path)
        writer.writerow(list(schema['properties'].keys()))
        if elements:
            for element in elements:
                writer.writerow(self.format_values(list(element.dict().values())))
