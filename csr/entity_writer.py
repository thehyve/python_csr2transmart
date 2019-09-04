import logging
import os
from os import path
from typing import Optional, Sequence, Dict

from pydantic import BaseModel
from sources2csr.data_exception import DataException
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

    def write_entities(self, filename: str, schema: Dict, elements: Optional[Sequence[BaseModel]]):
        output_path = self.output_dir + '/' + filename
        if path.exists(output_path):
            raise DataException('File already exists: {}'.format(output_path))
        writer: TsvWriter = TsvWriter(output_path)
        writer.writerow(list(schema['properties'].keys()))
        if elements:
            for element in elements:
                writer.writerow(list(element.dict().values()))
