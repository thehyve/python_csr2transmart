from collections import Counter
from typing import Sequence, Optional

from csr.csr import SubjectEntity, StudyEntity
from pydantic import BaseModel, validator, constr


class OntologyConfigValidationException(ValueError):
    pass


class TreeNode(BaseModel):
    """
    Concept node
    """
    name: constr(min_length=1)
    concept_code: Optional[str]
    children: Optional[Sequence['TreeNode']]

    @validator('children', always=True)
    def check_consistency(cls, v, values):
        if v is not None and values.get('concept_code') is not None:
            raise OntologyConfigValidationException(f'Node cannot have both concept_code and children: {values}')
        if v is None and values.get('concept_code') is None:
            raise OntologyConfigValidationException(f'Node must have either concept_code or children: {values}')
        return v

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

    @validator('children', whole=True)
    def validate_child_names(cls, nodes: Optional[Sequence['TreeNode']]):
        if nodes is None:
            return nodes
        node_name_counts = Counter([node.name for node in nodes])
        duplicates = [k for k, v in node_name_counts.items() if v > 1]
        if duplicates:
            raise OntologyConfigValidationException(
                f'Duplicate child names: {", ".join(duplicates)}')
        return nodes


TreeNode.update_forward_refs()


class OntologyConfig(BaseModel):
    """
    Ontology tree configuration
    """
    nodes: Sequence[TreeNode]

    @validator('nodes', whole=True)
    def validate_node_names(cls, nodes: Sequence[TreeNode]):
        node_name_counts = Counter([node.name for node in nodes])
        duplicates = [k for k, v in node_name_counts.items() if v > 1]
        if duplicates:
            raise OntologyConfigValidationException(
                f'Duplicate node names: {", ".join(duplicates)}')
        return nodes
