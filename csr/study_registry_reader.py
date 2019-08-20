import logging
from os import path

from csr.csr import CentralSubjectRegistry, Individual, Diagnosis, Biosource, Biomaterial
from csr.entity_reader import EntityReader

logger = logging.getLogger(__name__)


class SubjectRegistryReader(EntityReader):
    """Reader that reads Central Subject Registry (CSR) data from tab delimited files.
    """

    def __init__(self, input_dir: str):
        EntityReader.__init__(self, input_dir)

    def read_subject_registry(self) -> CentralSubjectRegistry:
        try:
            individuals = self.read_entities(path.join(self.input_dir, 'individual.tsv'), Individual)
            diagnoses = self.read_entities(path.join(self.input_dir, 'diagnosis.tsv'), Diagnosis)
            biosources = self.read_entities(path.join(self.input_dir, 'biosource.tsv'), Biosource)
            biomaterials = self.read_entities(path.join(self.input_dir, 'biomaterial.tsv'), Biomaterial)
            return CentralSubjectRegistry(individuals=individuals,
                                          diagnoses=diagnoses,
                                          biosources=biosources,
                                          biomaterials=biomaterials)
        except FileNotFoundError as fnfe:
            raise FileNotFoundError('File not found. {}'.format(fnfe))
