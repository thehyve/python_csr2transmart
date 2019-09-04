from csr.csr import CentralSubjectRegistry, Individual, Diagnosis, Biosource, Biomaterial
from csr.entity_writer import EntityWriter


class SubjectRegistryWriter(EntityWriter):
    """Writer that writes Central Subject Registry (CSR) data to tab delimited files.
    """

    def __init__(self, output_dir: str):
        EntityWriter.__init__(self, output_dir)

    def write(self, subject_registry: CentralSubjectRegistry):
        self.write_entities('individual.tsv', Individual.schema(), subject_registry.individuals)
        self.write_entities('diagnosis.tsv', Diagnosis.schema(), subject_registry.diagnoses)
        self.write_entities('biosource.tsv', Biosource.schema(), subject_registry.biosources)
        self.write_entities('biomaterial.tsv', Biomaterial.schema(), subject_registry.biomaterials)
