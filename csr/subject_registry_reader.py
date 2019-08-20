import logging

from csr.csr import StudyRegistry, Study, IndividualStudy
from csr.entity_reader import EntityReader

logger = logging.getLogger(__name__)


class StudyRegistryReader(EntityReader):
    """Reader that reads study registry data from tab delimited files.
    """

    def __init__(self, input_dir: str):
        EntityReader.__init__(self, input_dir)

    def read_subject_registry(self) -> StudyRegistry:
        try:
            studies = self.read_entities('{}/{}'.format(self.input_dir, 'study.tsv'), Study)
            individual_studies = self.read_entities('{}/{}'.format(self.input_dir, 'individual_study.tsv'),
                                                    IndividualStudy)
            return StudyRegistry(studies=studies,
                                 individual_studies=individual_studies)
        except FileNotFoundError as fnfe:
            raise FileNotFoundError('File not found. {}'.format(fnfe))
