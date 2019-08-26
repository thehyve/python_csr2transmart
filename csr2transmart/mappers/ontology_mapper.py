from typing import List, Dict, Sequence

from transmart_loader.transmart import Concept, TreeNode, ValueType, ConceptNode

from csr.csr import SubjectEntity, StudyEntity
from csr2transmart.ontology_config import TreeNode as OntologyConfigTreeNode, \
    ConceptNode as OntologyConfigConceptNode


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
    def is_concept_node(node):
        if isinstance(node, dict):
            return node.get('concept_code') is not None
        else:
            return isinstance(node, OntologyConfigConceptNode) and node.concept_code is not None

    def get_concept_type(self, entity_name: str, entity_field_name: str) -> ValueType:
        entity_types = list(SubjectEntity.__args__)
        entity_types.extend(list(StudyEntity.__args__))
        entity_type: SubjectEntity = list(filter(lambda x: x.schema()['title'] == entity_name, entity_types))[0]
        field_type = entity_type.schema()['properties'][entity_field_name]['type']
        return self.type_to_value_type(field_type)

    def map_code(self, node: OntologyConfigConceptNode, path_elements: List[str]) -> ConceptNode:
        entity_name, entity_field_name = node.concept_code.split('.')
        path_elements.append(entity_field_name)
        concept_path = '\\'.join(path_elements)
        concept_type = self.get_concept_type(entity_name, entity_field_name)

        concept = Concept(node.concept_code, node.name, concept_path, concept_type)
        self.concept_code_to_concept[node.concept_code] = concept
        return ConceptNode(concept)

    #  TODO: - fix mapping of ontology nodes so all of them instance of OntologyConfigTreeNode class, not dict
    #        - check if concept exists in the csr model (for a specific subject_dimension) - pydantic validator?
    def map_nodes(self, nodes: Sequence[OntologyConfigTreeNode], parent_node: TreeNode, path_elements: List[str]):
        for node in nodes:
            children_path = path_elements.copy()
            if self.is_concept_node(node):
                if isinstance(node, dict):
                    node = OntologyConfigConceptNode(**node)
                parent_node.add_child(self.map_code(node, path_elements))
            else:
                if isinstance(node, dict):
                    name = node.get('name')
                    children = node.get('children')
                else:
                    name = node.name
                    children = node.children
                children_path.append(name)
                intermediate_node = TreeNode(name)
                self.map_nodes(children, intermediate_node, children_path)
                parent_node.add_child(intermediate_node)

    def map(self, src_nodes: Sequence[OntologyConfigTreeNode]) -> Sequence[TreeNode]:
        path = [self.top_tree_node]
        top_node = TreeNode(self.top_tree_node)
        self.map_nodes(src_nodes, top_node, path)
        return [top_node]
