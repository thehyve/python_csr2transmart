import datetime
from typing import Dict, Sequence, Optional

from transmart_loader.transmart import Concept, TreeNode, ValueType, ConceptNode, TreeNodeMetadata

from csr.csr import SubjectEntity, StudyEntity
from csr2transmart.ontology_config import TreeNode as OntologyConfigTreeNode, OntologyConfigValidationException

subject_entity_names = list(map(lambda se: se.schema()['title'], SubjectEntity.__args__))


class OntologyMapper:
    """
    Map ontology config to tree nodes and concepts
    """
    def __init__(self, top_tree_node: str):
        self.top_tree_node = top_tree_node
        self.concept_code_to_concept: Dict[str, Concept] = {}

    @staticmethod
    def field_to_value_type(field: Dict) -> ValueType:
        if field['type'] in ['integer', 'number']:
            return ValueType.Numeric
        if field['type'] == 'string' and field.get('format') == 'date':
            return ValueType.Date
        else:
            return ValueType.Categorical

    @staticmethod
    def get_metadata_for_entity(entity_name: str) -> Optional[TreeNodeMetadata]:
        if entity_name == 'Individual':
            return TreeNodeMetadata({'subject_dimension': 'patient'})
        elif entity_name in subject_entity_names:
            return TreeNodeMetadata({'subject_dimension': entity_name})
        return None

    @staticmethod
    def is_concept_node(node: OntologyConfigTreeNode) -> bool:
        return node.concept_code is not None

    def get_concept_type(self, entity_name: str, entity_field_name: str) -> ValueType:
        entity_types = list(SubjectEntity.__args__)
        entity_types.extend(list(StudyEntity.__args__))
        entity_type: SubjectEntity = list(filter(lambda x: x.schema()['title'] == entity_name, entity_types))[0]
        field = entity_type.schema()['properties'][entity_field_name]
        return self.field_to_value_type(field)

    def map_concept_node(self, node: OntologyConfigTreeNode) -> ConceptNode:
        entity_name, entity_field_name = node.concept_code.split('.')
        concept_path = '\\CSR\\' + node.concept_code
        concept_type = self.get_concept_type(entity_name, entity_field_name)
        concept = Concept(node.concept_code, node.name, concept_path, concept_type)
        self.concept_code_to_concept[node.concept_code] = concept

        concept_node = ConceptNode(concept)
        concept_node.metadata = self.get_metadata_for_entity(entity_name)
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
        root_node: Optional[TreeNode] = None
        top_node: Optional[TreeNode] = None
        path = self.top_tree_node.split('\\')
        for node in path:
            if not node:
                # Skip empty path elements
                continue
            current_node = TreeNode(node)
            if top_node:
                top_node.add_child(current_node)
            else:
                root_node = current_node
            top_node = current_node
        if not top_node:
            raise OntologyConfigValidationException(f'Invalid top tree node: {self.top_tree_node}')
        date = datetime.datetime.now().strftime('%d-%m-%Y')
        top_node.metadata = TreeNodeMetadata({'Load date': date})
        self.map_nodes(src_nodes, top_node)
        return [root_node]
