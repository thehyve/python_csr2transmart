import random
import string
from typing import List, Dict
from transmart_loader.transmart import Patient, Concept, TreeNode, ValueType, ConceptNode
from csr2transmart.blueprint import Blueprint, ForceCategoricalBoolean, BlueprintElement


class BlueprintMapper:
    """
    Map blueprint and CSR DataFrame to concepts and ontology tree in transmart-loader format
    """
    def __init__(self, individual_id_to_patient: Dict[str, Patient], top_tree_node: str):
        self.top_tree_node = top_tree_node
        self.individual_id_to_patient: Dict[str, Patient] = individual_id_to_patient
        self.concept_key_to_modifier_key: Dict[str, str] = {}
        self.concept_key_to_concept: Dict[str, Concept] = {}
        self.ontology: List[TreeNode] = [TreeNode(top_tree_node)]

    def map_code(self, concept_key: str, blueprint_element: BlueprintElement):
        path_elements = blueprint_element.path.split('+')
        path = '\\'.join(path_elements)
        concept_path = '\\' + self.top_tree_node + '\\'.join([path])

        concept_type = ValueType.Categorical if \
            blueprint_element.force_categorical == ForceCategoricalBoolean.ForceTrue else ValueType.Numeric
        name = blueprint_element.label
        # TODO replace concept_code with entity name + field name
        concept = Concept(''.join((random.choice(string.ascii_lowercase) for i in range(10))),
                          name, concept_path, concept_type)

        self.concept_key_to_concept[concept_key] = concept
        self.map_concept_node(concept, path_elements)

    def map_concept_node(self, concept: Concept, path_elements: List[str]):
        intermediate_nodes = list(map(lambda x: TreeNode(x), path_elements))
        intermediate_nodes[-1].add_child(ConceptNode(concept))
        i = 1
        while i < len(intermediate_nodes):
            intermediate_nodes[i].add_child(intermediate_nodes[i-1])
            i += 1
        self.ontology[0].add_child(intermediate_nodes[0])

    def map(self, blueprint: Blueprint):
        non_concept_blueprint_labels = ['SUBJ_ID', 'OMIT', 'MODIFIER']
        for concept_key, blueprint_element in blueprint.items():
            # TODO check if concept exists in the csr model (for a specific subject_dimension)
            if blueprint_element.label not in non_concept_blueprint_labels:
                self.map_code(concept_key, blueprint_element)
                self.concept_key_to_modifier_key[concept_key] = blueprint_element.metadata_tags['subject_dimension']
