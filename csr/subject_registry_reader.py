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
            study_dicts = self.read_entities('{}/{}'.format(self.input_dir, 'study.tsv'), Study.schema())
            studies = list(map(lambda i: Study(**i), study_dicts))

            individual_study_dicts = self.read_entities('{}/{}'.format(self.input_dir, 'individual_study.tsv'),
                                                        IndividualStudy.schema())
            individual_studies = list(map(lambda i: IndividualStudy(**i), individual_study_dicts))

            return StudyRegistry(studies=studies,
                                 individual_studies=individual_studies)
        except FileNotFoundError as fnfe:
            raise FileNotFoundError('File not found. {}'.format(fnfe))
