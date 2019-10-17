from csr.csr import CentralSubjectRegistry, SubjectEntity
from csr.entity_writer import EntityWriter
from csr.snake_case import camel_case_to_snake_case


class SubjectRegistryWriter(EntityWriter):
    """Writer that writes Central Subject Registry (CSR) data to tab delimited files.
    """

    def __init__(self, output_dir: str):
        EntityWriter.__init__(self, output_dir)

    def write(self, subject_registry: CentralSubjectRegistry):
        for entity_type in list(SubjectEntity.__args__):
            schema = entity_type.schema()
            name = schema['title']
            filename = f'{camel_case_to_snake_case(name)}.tsv'
            self.write_entities(filename, schema, subject_registry.entity_data[name])
