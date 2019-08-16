import logging

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
            individual_dicts = self.read_entities('{}/{}'.format(self.input_dir, 'individual.tsv'), Individual.schema())
            individuals = list(map(lambda i: Individual(**i), individual_dicts))

            diagnosis_dicts = self.read_entities('{}/{}'.format(self.input_dir, 'diagnosis.tsv'), Diagnosis.schema())
            diagnoses = list(map(lambda i: Diagnosis(**i), diagnosis_dicts))

            biosource_dicts = self.read_entities('{}/{}'.format(self.input_dir, 'biosource.tsv'), Biosource.schema())
            biosources = list(map(lambda i: Biosource(**i), biosource_dicts))

            biomaterial_dicts = self.read_entities('{}/{}'.format(self.input_dir, 'biomaterial.tsv'),
                                                   Biomaterial.schema())
            biomaterials = list(map(lambda i: Biomaterial(**i), biomaterial_dicts))

            return CentralSubjectRegistry(individuals=individuals,
                                          diagnoses=diagnoses,
                                          biosources=biosources,
                                          biomaterials=biomaterials)
        except FileNotFoundError as fnfe:
            raise FileNotFoundError('File not found. {}'.format(fnfe))
