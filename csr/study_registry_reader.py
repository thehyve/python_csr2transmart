import logging
from os import path
from typing import Type

from csr.csr import StudyRegistry, StudyEntity
from csr.entity_reader import EntityReader
from csr.snake_case import camel_case_to_snake_case

logger = logging.getLogger(__name__)


def entity_filename(entity_type: Type[StudyEntity]):
    title = entity_type.schema()['title']
    return f'{camel_case_to_snake_case(title)}.tsv'


class StudyRegistryReader(EntityReader):
    """Reader that reads study registry data from tab delimited files.
    """

    def __init__(self, input_dir: str):
        EntityReader.__init__(self, input_dir)

    def read_study_registry(self) -> StudyRegistry:
        try:
            entity_data = {entity_type.schema()['title']:
                           self.read_entities(path.join(self.input_dir, entity_filename(entity_type)), entity_type)
                           for entity_type in list(StudyEntity.__args__)}
            return StudyRegistry(entity_data=entity_data)
        except FileNotFoundError as fnfe:
            raise FileNotFoundError('File not found. {}'.format(fnfe))
