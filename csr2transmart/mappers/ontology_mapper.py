import datetime
from typing import Dict, Sequence

from transmart_loader.transmart import Concept, TreeNode, ValueType, ConceptNode, TreeNodeMetadata

from csr.csr import SubjectEntity, StudyEntity
from csr2transmart.ontology_config import TreeNode as OntologyConfigTreeNode, OntologyConfigValidationException


class OntologyMapper:
    """
    Map ontology config to tree nodes and concepts
    """
    def __init__(self, top_tree_node: str):
        self.top_tree_node = top_tree_node
        self.concept_code_to_concept: Dict[str, Concept] = {}

    @staticmethod
    def type_to_value_type(field_type) -> ValueType:
        if field_type in ['integer', 'number']:
            return ValueType.Numeric
        if field_type in ['date']:
            return ValueType.Date
        else:
            return ValueType.Categorical

    @staticmethod
    def entity_name_to_subject_dimension_value(entity_name: str) -> str:
        if entity_name == 'Individual':
            return 'patient'
        else:
            return entity_name

    @staticmethod
    def is_concept_node(node: OntologyConfigTreeNode) -> bool:
        return node.concept_code is not None

    def get_concept_type(self, entity_name: str, entity_field_name: str) -> ValueType:
        entity_types = list(SubjectEntity.__args__)
        entity_types.extend(list(StudyEntity.__args__))
        entity_type: SubjectEntity = list(filter(lambda x: x.schema()['title'] == entity_name, entity_types))[0]
        field_type = entity_type.schema()['properties'][entity_field_name]['type']
        return self.type_to_value_type(field_type)

    def map_concept_node(self, node: OntologyConfigTreeNode) -> ConceptNode:
        entity_name, entity_field_name = node.concept_code.split('.')
        concept_path = '\\\\CSR\\\\' + node.concept_code
        concept_type = self.get_concept_type(entity_name, entity_field_name)
        concept = Concept(node.concept_code, node.name, concept_path, concept_type)
        self.concept_code_to_concept[node.concept_code] = concept

        metadata_value: Dict[str, str] = {
            'subject_dimension': self.entity_name_to_subject_dimension_value(entity_name)}
        concept_node = ConceptNode(concept)
        concept_node.metadata = TreeNodeMetadata(metadata_value)
        return concept_node

    def map_nodes(self, nodes: Sequence[OntologyConfigTreeNode], parent_node: TreeNode):
        for node in nodes:
            if isinstance(node, dict):
                node = OntologyConfigTreeNode(**node)
            elif not isinstance(node, OntologyConfigTreeNode):
                raise OntologyConfigValidationException(f'Invalid ontology node: {node}')

            if self.is_concept_node(node):
                parent_node.add_child(self.map_concept_node(node))
            else:
                intermediate_node = TreeNode(node.name)
                self.map_nodes(node.children, intermediate_node)
                parent_node.add_child(intermediate_node)

    def map(self, src_nodes: Sequence[OntologyConfigTreeNode]) -> Sequence[TreeNode]:
        date = datetime.datetime.now().strftime('%d-%m-%Y')
        metadata = TreeNodeMetadata({'Load date': date})
        top_node = TreeNode(self.top_tree_node, metadata)
        self.map_nodes(src_nodes, top_node)
        return [top_node]
