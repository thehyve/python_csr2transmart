import datetime
import random
import string
from typing import List, Dict, Optional
from pandas import DataFrame
from transmart_loader.transmart import DataCollection, Study, TrialVisit, Patient, Concept, Modifier, Dimension, \
    TreeNode, Observation, ValueType, DimensionType, ObservationMetadata, Value, CategoricalValue, NumericalValue, \
    ConceptNode, IdentifierMapping, StudyMetadata, DateValue, TextValue

from csr2transmart.blueprint import Blueprint, ForceCategoricalBoolean, BlueprintElement


def type_to_value_type(value: str) -> ValueType:
    if value is not None and value.lower() == 'numeric':
        return ValueType.Numeric
    else:
        return ValueType.Categorical


def type_to_dimension_type(dimension_type: str) -> DimensionType:
    if dimension_type is not None and dimension_type.lower() == 'subject':
        return DimensionType.Subject
    else:
        return DimensionType.Attribute


def row_value_to_value(concept_col, value_type: ValueType) -> Optional[Value]:
    if concept_col is None:
        return None
    if value_type is ValueType.Categorical:
        return CategoricalValue(concept_col)
    elif value_type is ValueType.Numeric:
        return NumericalValue(concept_col)
    elif value_type is ValueType.DateValue:
        return DateValue(concept_col)
    else:
        return TextValue(concept_col)


class CsrMapper:
    """
    Map CSR data to Transmart Loader input format
    """
    def __init__(self, study_id: str, top_tree_node: str):
        self.default_trial_visit_label = 'GENERAL'
        self.patient_col = 'INDIVIDUAL_ID'
        self.study_id = study_id
        self.top_tree_node = top_tree_node
        self.individual_id_to_patient: Dict[str, Patient] = {}

    @staticmethod
    def get_study_metadata() -> StudyMetadata:
        # Add loading date to metadata
        date = datetime.datetime.now().strftime('%d-%m-%Y')
        return StudyMetadata({'Load date': date})

    @staticmethod
    def map_observation_metadata(modifier_key, modifier_key_to_modifier, row) -> Optional[ObservationMetadata]:
        if modifier_key is None or modifier_key is not 'patient':
            return None
        mod_metadata: Dict[Modifier, Value] = dict()
        value = row.get(modifier_key)
        modifier = modifier_key_to_modifier.get(modifier_key)
        if modifier is None:
            return None
        mod_metadata[modifier] = CategoricalValue(value) if \
            modifier.value_type == ValueType.Categorical else NumericalValue(value)
        return ObservationMetadata(mod_metadata)

    def map_study(self) -> Study:
        metadata = self.get_study_metadata()
        return Study(self.study_id, self.study_id, metadata)

    def map_default_trial_visit(self, study: Study) -> TrialVisit:
        return TrialVisit(study, self.default_trial_visit_label)

    def map_patients(self, csr_df: DataFrame) -> List[Patient]:
        patients: List[Patient] = []
        sex_col = 'GENDER'
        for index, row in csr_df.iterrows():
            mapping = IdentifierMapping('SUB_ID', row[self.patient_col])
            patient = Patient(index, row[sex_col], [mapping])
            self.individual_id_to_patient[row[self.patient_col]] = patient
            patients.append(patient)
        return patients

    def map_observations(self,
                         csr_df: DataFrame,
                         default_trial_visit: TrialVisit,
                         concept_key_to_concept: Dict[str, Concept],
                         modifier_key_to_modifier: Dict[str, Modifier],
                         concept_key_to_modifier_key: Dict[str, str]):
        observations: List[Observation] = []
        for index, row in csr_df.iterrows():
            patient = self.individual_id_to_patient[row[self.patient_col]]
            for concept_col, concept in concept_key_to_concept.items():
                value = row_value_to_value(row.get(concept_col), concept.value_type)
                if row.get(concept_col) is not None:
                    modifier_key = concept_key_to_modifier_key.get(concept_col)
                    metadata = self.map_observation_metadata(modifier_key, modifier_key_to_modifier, row)
                    observations.append(
                        Observation(patient, concept, None, default_trial_visit, None, None, value, metadata))
        return observations

    def map(self, csr_df: DataFrame, modifiers: DataFrame, blueprint: Blueprint) -> DataCollection:
        study = self.map_study()
        default_trial_visit = self.map_default_trial_visit(study)
        patients = self.map_patients(csr_df)
        modifier_mapper = ModifierMapper()
        modifier_mapper.map(modifiers)
        bp_mapper = BlueprintMapper(self.individual_id_to_patient, self.top_tree_node)
        bp_mapper.map(blueprint, csr_df)
        observations = self.map_observations(csr_df,
                                             default_trial_visit,
                                             bp_mapper.concept_key_to_concept,
                                             modifier_mapper.modifier_key_to_modifier,
                                             bp_mapper.concept_key_to_modifier_key)

        return DataCollection(bp_mapper.concept_key_to_concept.values(),
                              modifier_mapper.modifier_key_to_modifier.values(),
                              modifier_mapper.dimensions,
                              [study],
                              [default_trial_visit],
                              [],
                              bp_mapper.ontology,
                              patients,
                              observations,
                              [],
                              [])


class ModifierMapper:
    """
    Map modifiers file to transmart-loader Modifier and Dimension classes
    """
    def __init__(self):
        self.dimensions: List[Dimension] = []
        self.modifier_key_to_modifier: Dict[str, Modifier] = {}

    def map(self, modifiers: DataFrame):
        modifier_code_col = 'modifier_cd'
        name_col = 'name_char'
        modifier_path_col = 'modifier_path'
        dimension_type_col = 'dimension_type'
        sort_index_col = 'sort_index'
        value_type_col = 'Data Type'

        for index, row in modifiers.iterrows():
            modifier = Modifier(row.get(modifier_code_col),
                                row.get(name_col),
                                row.get(modifier_path_col),
                                type_to_value_type(row.get(value_type_col)))
            self.modifier_key_to_modifier[row[name_col]] = modifier

            modifier_dimension = Dimension(row.get(name_col),
                                           modifier,
                                           type_to_dimension_type(row.get(dimension_type_col)),
                                           row.get(sort_index_col))
            self.dimensions.append(modifier_dimension)


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

    def map_codes(self, concept_key: str, blueprint_element: BlueprintElement):
        path_elements = blueprint_element.get('path').split('+')
        path = '\\'.join(path_elements)

        concept_path = '\\' + self.top_tree_node + '\\'.join([path])
        concept_type = ValueType.Categorical if \
            blueprint_element.get('force_categorical') == ForceCategoricalBoolean.ForceTrue else ValueType.Numeric
        name = blueprint_element.get('label')
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

    def map(self, blueprint: Blueprint, csr_df: DataFrame):
        non_concept_blueprint_labels = ['SUBJ_ID', 'OMIT', 'MODIFIER']
        concept_columns = [key for (key, value) in blueprint.items() if value.get('label')
                           not in non_concept_blueprint_labels]
        for col in csr_df.columns:
            if col in concept_columns:
                blueprint_element = blueprint.get(col)
                self.map_codes(col, blueprint_element)
                self.concept_key_to_modifier_key[col] = blueprint_element.get('metadata_tags')['subject_dimension']
