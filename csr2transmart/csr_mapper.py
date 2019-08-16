import datetime
import random
import string
from typing import List, Dict, Optional, Sequence, Any
from pandas import DataFrame
from transmart_loader.transmart import DataCollection, Study, TrialVisit, Patient, Concept, Modifier, Dimension, \
    TreeNode, Observation, ValueType, DimensionType, ObservationMetadata, Value, CategoricalValue, NumericalValue, \
    ConceptNode, IdentifierMapping, StudyMetadata, DateValue, TextValue

from csr.csr import CentralSubjectRegistry, StudyRegistry, Individual, Diagnosis, Biosource, Biomaterial
from csr2transmart.blueprint import Blueprint, ForceCategoricalBoolean, BlueprintElement


class CsrMappingException(Exception):
    pass


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


def row_value_to_value(row_value, value_type: ValueType) -> Optional[Value]:
    if row_value is None:
        return None
    if value_type is ValueType.Categorical:
        return CategoricalValue(row_value)
    elif value_type is ValueType.Numeric:
        return NumericalValue(row_value)
    elif value_type is ValueType.DateValue:
        return DateValue(row_value)
    else:
        return TextValue(row_value)


class ObservationMapper:
    """
    Map observations for subject registry and study registry
    """
    def __init__(self,
                 default_trial_visit: TrialVisit,
                 individual_id_to_patient: Dict[str, Patient],
                 concept_key_to_concept: Dict[str, Concept],
                 concept_key_to_modifier_key: Dict[str, str],
                 modifier_key_to_modifier: Dict[str, Modifier]):
        self.default_trial_visit = default_trial_visit
        self.individual_id_to_patient = individual_id_to_patient
        self.concept_key_to_concept = concept_key_to_concept
        self.concept_key_to_modifier_key = concept_key_to_modifier_key
        self.modifier_key_to_modifier = modifier_key_to_modifier
        self.observations: List[Observation] = []

    def map_observation_metadata(self, modifier_key, value: str) -> Optional[ObservationMetadata]:
        if modifier_key is None or value is None:
            return None
        mod_metadata: Dict[Modifier, Value] = dict()
        modifier = self.modifier_key_to_modifier.get(modifier_key)
        if modifier is None:
            return None
        mod_metadata[modifier] = CategoricalValue(value)
        return ObservationMetadata(mod_metadata)

    def add_observations_for_entity(self, entity, entity_id: str, patient: Patient):
        concept_keys = entity.fields.keys()
        for concept_key in concept_keys:
            concept = self.concept_key_to_concept.get(concept_key.upper())
            if concept is not None:
                value = row_value_to_value(getattr(entity, concept_key), concept.value_type)
                if value is not None:
                    if isinstance(entity, Individual):
                        metadata = None
                    else:
                        modifier_key = self.concept_key_to_modifier_key.get(concept_key.upper())
                        metadata = self.map_observation_metadata(modifier_key, entity_id)
                    observation = Observation(patient, concept, None, self.default_trial_visit, None, None, value,
                                              metadata)
                    self.observations.append(observation)

    def map_individual_linked_entity_observations(self, entities: Sequence[Any], id_attribute: str):
        for entity in entities:
            entity_id = getattr(entity, id_attribute)
            patient = self.individual_id_to_patient.get(entity.individual_id)
            if patient is None:
                raise CsrMappingException('No patient with identifier: {}. '
                                          'Skipping creating observation for {} with id: {}. Entity {}, Ind {}'
                                          .format(entity.individual_id, type(entity).__name__, entity_id,
                                                  entity, self.individual_id_to_patient.keys()))
            self.add_observations_for_entity(entity, entity_id, patient)

    def map_biomaterial_observations(self, biomaterials: Sequence[Biomaterial], biosources: Sequence[Biosource]):
        for biomaterial in biomaterials:
            linked_biosource = next((bs for bs in biosources if bs.biosource_id == biomaterial.src_biosource_id), None)
            if linked_biosource is None:
                raise CsrMappingException('No biosource linked to biomaterial with id: {}. '
                                          'Skipping creating observation.'.format(biomaterial.biomaterial_id))
            patient = self.individual_id_to_patient.get(linked_biosource.individual_id)
            if patient is None:
                raise CsrMappingException('No patient with identifier: {}. '
                                          'Skipping creating observation for Biomaterial with id: {}.'
                                          .format(linked_biosource.individual_id, biomaterial.biomaterial_id))
            self.add_observations_for_entity(biomaterial, biomaterial.biomaterial_id, patient)

    def map_study_registry_observations(self, study_registry: StudyRegistry):
        for ind_study in study_registry.individual_studies:
            study = next((s for s in study_registry.studies if s.study_id == ind_study.study_id), None)
            if study is None:
                raise CsrMappingException('No study with identifier: {}. '
                                          'Skipping creating observation for individual study with id: {}.'
                                          .format(ind_study.study_id, ind_study.individual_id))
            patient = self.individual_id_to_patient.get(ind_study.individual_id)
            if patient is None:
                raise CsrMappingException('No patient with identifier: {}. '
                                          'Skipping creating observation for study with id: {}.'
                                          .format(ind_study.individual_id, ind_study.individual_id))
            self.add_observations_for_entity(study, study.study_id, patient)

    def map_observations(self, subject_registry: CentralSubjectRegistry, study_registry: StudyRegistry):
        self.map_individual_linked_entity_observations(subject_registry.individuals, 'individual_id')
        self.map_individual_linked_entity_observations(subject_registry.diagnoses, 'diagnosis_id')
        self.map_individual_linked_entity_observations(subject_registry.biosources, 'biosource_id')
        self.map_biomaterial_observations(subject_registry.biomaterials, subject_registry.biosources)
        self.map_study_registry_observations(study_registry)


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

    def map_study(self) -> Study:
        metadata = self.get_study_metadata()
        return Study(self.study_id, self.study_id, metadata)

    def map_default_trial_visit(self, study: Study) -> TrialVisit:
        return TrialVisit(study, self.default_trial_visit_label)

    def map_patients(self, individuals: Sequence[Individual]):
        for individual in individuals:
            mapping = IdentifierMapping('SUB_ID', individual.individual_id)
            patient = Patient(individual.individual_id, individual.gender, [mapping])
            self.individual_id_to_patient[individual.individual_id] = patient

    def map(self,
            subject_registry: CentralSubjectRegistry,
            study_registry: StudyRegistry,
            modifiers: DataFrame,
            blueprint: Blueprint) -> DataCollection:
        self.map_patients(subject_registry.individuals)
        study = self.map_study()
        default_trial_visit = self.map_default_trial_visit(study)

        modifier_mapper = ModifierMapper()
        modifier_mapper.map(modifiers)

        bp_mapper = BlueprintMapper(self.individual_id_to_patient, self.top_tree_node)
        bp_mapper.map(blueprint)

        observation_mapper = ObservationMapper(default_trial_visit,
                                               self.individual_id_to_patient,
                                               bp_mapper.concept_key_to_concept,
                                               bp_mapper.concept_key_to_modifier_key,
                                               modifier_mapper.modifier_key_to_modifier)
        observation_mapper.map_observations(subject_registry, study_registry)

        return DataCollection(bp_mapper.concept_key_to_concept.values(),
                              modifier_mapper.modifier_key_to_modifier.values(),
                              modifier_mapper.dimensions,
                              [study],
                              [default_trial_visit],
                              [],
                              bp_mapper.ontology,
                              self.individual_id_to_patient.values(),
                              observation_mapper.observations,
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

    def map_code(self, concept_key: str, blueprint_element: BlueprintElement):
        path_elements = blueprint_element.path.split('+')
        path = '\\'.join(path_elements)
        concept_path = '\\' + self.top_tree_node + '\\'.join([path])

        concept_type = ValueType.Categorical if \
            blueprint_element.force_categorical == ForceCategoricalBoolean.ForceTrue else ValueType.Numeric
        name = blueprint_element.label
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
