from typing import Sequence, Optional

from csr.csr import SubjectEntity, StudyEntity
from pydantic import BaseModel, validator


class OntologyConfigValidationException(Exception):
    pass


class TreeNode(BaseModel):
    """
    Ontology node
    """
    name: str
    children: Optional[Sequence['TreeNode']]


class ConceptNode(TreeNode):
    """
    Concept ontology node
    """
    concept_code: str

    @validator('concept_code')
    def check_valid_in_csr(cls, concept_code):
        entity_name_field_pair = concept_code.split('.')
        if len(entity_name_field_pair) != 2:
            raise OntologyConfigValidationException(f'Invalid concept code format: {concept_code}. '
                                                    f'Concept code has to have format: `<entity_name>.<entity_field>`')

        csr_entities = list(SubjectEntity.__args__) + list(StudyEntity.__args__)
        csr_entity_names = list(map(lambda se: se.schema()['title'], csr_entities))
        if entity_name_field_pair[0] not in csr_entity_names:
            raise OntologyConfigValidationException(f'Invalid concept code: {concept_code}. '
                                                    f'{entity_name_field_pair[0]} is not a valid CSR entity.')

        csr_entity_fields = list(filter(lambda e: e.schema()['title'] == entity_name_field_pair[0],
                                        csr_entities))[0].schema()['properties'].keys()
        if entity_name_field_pair[1] not in csr_entity_fields:
            raise OntologyConfigValidationException(f'Invalid concept code: {concept_code}. '
                                                    f'Field: {entity_name_field_pair[1]} '
                                                    f'is not a valid field of {entity_name_field_pair[0]} entity.')
        return concept_code


class OntologyConfig(BaseModel):
    """
    Ontology tree configuration
    """
    nodes: Sequence[TreeNode]
