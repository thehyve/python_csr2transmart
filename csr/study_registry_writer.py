from csr.csr import StudyRegistry, Study, IndividualStudy
from csr.entity_writer import EntityWriter


class StudyRegistryWriter(EntityWriter):
    """Writer that writes study registry data to tab delimited files.
    """

    def __init__(self, output_dir: str):
        EntityWriter.__init__(self, output_dir)

    def write(self, study_registry: StudyRegistry):
        # Write studies
        self.write_entities('study.tsv', Study.schema(), study_registry.studies)
        # Write individual-study links
        self.write_entities('individual_study.tsv', IndividualStudy.schema(), study_registry.individual_studies)
