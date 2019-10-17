from csr.csr import StudyRegistry, StudyEntity
from csr.entity_writer import EntityWriter
from csr.snake_case import camel_case_to_snake_case


class StudyRegistryWriter(EntityWriter):
    """Writer that writes study registry data to tab delimited files.
    """

    def __init__(self, output_dir: str):
        EntityWriter.__init__(self, output_dir)

    def write(self, study_registry: StudyRegistry):
        for entity_type in list(StudyEntity.__args__):
            schema = entity_type.schema()
            name = schema['title']
            filename = f'{camel_case_to_snake_case(name)}.tsv'
            self.write_entities(filename, schema, study_registry.entity_data[name])
