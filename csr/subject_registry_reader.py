import logging
from os import path
from typing import Type

from csr.csr import CentralSubjectRegistry, SubjectEntity
from csr.entity_reader import EntityReader
from csr.snake_case import camel_case_to_snake_case

logger = logging.getLogger(__name__)


def entity_filename(entity_type: Type[SubjectEntity]):
    title = entity_type.schema()['title']
    return f'{camel_case_to_snake_case(title)}.tsv'


class SubjectRegistryReader(EntityReader):
    """Reader that reads Central Subject Registry (CSR) data from tab delimited files.
    """

    def __init__(self, input_dir: str):
        EntityReader.__init__(self, input_dir)

    def read_subject_registry(self) -> CentralSubjectRegistry:
        try:
            entity_data = {entity_type.schema()['title']:
                           self.read_entities(path.join(self.input_dir, entity_filename(entity_type)), entity_type)
                           for entity_type in list(SubjectEntity.__args__)}
            return CentralSubjectRegistry(entity_data=entity_data)
        except FileNotFoundError as fnfe:
            raise FileNotFoundError('File not found. {}'.format(fnfe))
