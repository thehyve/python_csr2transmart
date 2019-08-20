from typing import List, Dict, Optional, Sequence, Type
from pydantic import BaseModel
from transmart_loader.transmart import TrialVisit, Patient, Concept, Modifier, Observation, ObservationMetadata, \
    Value, CategoricalValue, ValueType, NumericalValue, DateValue, TextValue

from csr.csr import CentralSubjectRegistry, StudyRegistry, Individual, Diagnosis, Biosource, Biomaterial, SubjectEntity
from csr2transmart.csr_mapping_exception import CsrMappingException


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

    @staticmethod
    def row_value_to_value(row_value, value_type: ValueType) -> Optional[Value]:
        """
        Map entity value to transmart-loader Value by ValueType
        :param row_value: entity value
        :param value_type: transmart-loader ValueType
        :return: transmart-loader Value
        """
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

    @staticmethod
    def get_field_name_by_keyword(entity_type: Type[BaseModel], key: str, value) -> str:
        """
        Get name of the field of CSR entity type by the schema metadata
        :param entity_type: type of the CSR entity
        :param key: schema keyword key
        :param value: schema keyword value
        :return:
        """
        return list([name for (name, prop) in entity_type.schema()['properties'].items()
                     if key in prop and prop[key] is value])[0]

    def get_id_field_name(self, entity_type: Type[BaseModel]) -> str:
        """
        Get identifying field name of a CSR entity type by 'identity' schema keyword
        :param entity_type: type of the CSR entity
        :return:
        """
        return self.get_field_name_by_keyword(entity_type, 'identity', True)

    def get_ref_field_name(self, entity_type: Type[BaseModel], ref_type: str) -> str:
        """
        Get a name of the field referencing to entity of specified type
        :param entity_type: type of the CSR entity
        :param ref_type: name of the referencing entity type
        :return:
        """
        return self.get_field_name_by_keyword(entity_type, 'references', ref_type)

    def map_observation_metadata(self, modifier_key, value: str) -> Optional[ObservationMetadata]:
        """
        Get observation modifier
        :param modifier_key: observation modifier key
        :param value: value of the modifier observation
        :return: transmart-loader metadata if any
        """
        if modifier_key is None or value is None:
            return None
        mod_metadata: Dict[Modifier, Value] = dict()
        modifier = self.modifier_key_to_modifier.get(modifier_key)
        if modifier is None:
            return None
        mod_metadata[modifier] = CategoricalValue(value)
        return ObservationMetadata(mod_metadata)

    def map_observation(self, entity: BaseModel, entity_id: str, patient: Patient):
        """
        Map entity to trasmart-loader Observation
        :param entity: CSR entity
        :param entity_id: id of the entity
        :param patient: individual linked to the observation
        :return:
        """
        concept_keys = entity.fields.keys()
        for concept_key in concept_keys:
            concept = self.concept_key_to_concept.get(concept_key.upper())
            if concept is not None:
                value = self.row_value_to_value(getattr(entity, concept_key), concept.value_type)
                if value is not None:
                    if isinstance(entity, Individual):
                        metadata = None
                    else:
                        modifier_key = self.concept_key_to_modifier_key.get(concept_key.upper())
                        metadata = self.map_observation_metadata(modifier_key, entity_id)
                    observation = Observation(patient, concept, None, self.default_trial_visit, None, None, value,
                                              metadata)
                    self.observations.append(observation)

    def map_individual_linked_entity_observations(self, entities: Sequence[BaseModel]):
        """
        Map observations foe entities that have a direct linc to individuals,
        :param entities: Central subject registry entities
        :return:
        """
        if len(entities) > 0:
            entity_type = type(entities[0])
            id_attribute = self.get_id_field_name(entity_type)
            for entity in entities:
                entity_id = getattr(entity, id_attribute)
                patient = self.individual_id_to_patient.get(entity.individual_id)
                if patient is None:
                    raise CsrMappingException('No patient with identifier: {}. '
                                              'Failed to create observation for {} with id: {}. Entity {}, Ind {}'
                                              .format(entity.individual_id, type(entity).__name__, entity_id,
                                                      entity, self.individual_id_to_patient.keys()))
                self.map_observation(entity, entity_id, patient)

    def map_non_individual_linked_entity_observations(self,
                                                      entities: Sequence[SubjectEntity],
                                                      ref_entities: Sequence[SubjectEntity]):
        """
        Map observations foe entities that do not have a direct linc to individuals,
        but have a reference linking to individuals.
        :param entities: Central subject registry entities
        :param ref_entities: reference entities that have a link to individuals
        :return:
        """
        if len(entities) > 0:
            entity_type = type(entities[0])
            ref_entity_type = type(ref_entities[0])
            entity_id_field_name = self.get_id_field_name(entity_type)
            ref_id_field_name = self.get_id_field_name(ref_entity_type)
            entity_ref_field_name = self.get_ref_field_name(entity_type, ref_entity_type.schema()['title'])
            for entity in entities:
                entity_id = entity.__getattribute__(entity_id_field_name)
                linked_entity = next((
                    re for re in ref_entities
                    if entity.__getattribute__(entity_ref_field_name) == re.__getattribute__(ref_id_field_name)), None)
                if linked_entity is None:
                    raise CsrMappingException('No {} linked to {} with id: {}. '
                                              'Failed to create observation.'
                                              .format(ref_entity_type.schema()['title'],
                                                      entity_type.schema()['title'],
                                                      entity_id))
                patient = self.individual_id_to_patient.get(linked_entity.individual_id)
                if patient is None:
                    raise CsrMappingException('No patient with identifier: {}. '
                                              'Failed to create observation for {} with id: {}.'
                                              .format(linked_entity.individual_id, entity.schema()['title'],
                                                      entity_id))
                self.map_observation(entity, entity_id, patient)

    def map_study_registry_observations(self, study_registry: StudyRegistry):
        """
        Map observations for Subject registry entities
        :param study_registry: Study registry
        :return:
        """
        for ind_study in study_registry.individual_studies:
            study = next((s for s in study_registry.studies if s.study_id == ind_study.study_id), None)
            if study is None:
                raise CsrMappingException('No study with identifier: {}. '
                                          'Failed to create observation for individual study with id: {}.'
                                          .format(ind_study.study_id, ind_study.individual_id))
            patient = self.individual_id_to_patient.get(ind_study.individual_id)
            if patient is None:
                raise CsrMappingException('No patient with identifier: {}. '
                                          'Skipping creating observation for study with id: {}.'
                                          .format(ind_study.individual_id, ind_study.individual_id))
            self.map_observation(study, study.study_id, patient)

    def map_subject_registry_observations(self,
                                          entities: Sequence[SubjectEntity],
                                          ref_entities: Sequence[SubjectEntity] = []):
        """
        Map observations for Central subject registry entities
        :param entities: Central subject registry entities
        :param ref_entities: Optional, Central subject registry entities that link to individuals
        :return:
        """
        if len(ref_entities) == 0:
            self.map_individual_linked_entity_observations(entities)
        else:
            self.map_non_individual_linked_entity_observations(entities, ref_entities)

    def map_observations(self, subject_registry: CentralSubjectRegistry, study_registry: StudyRegistry):
        """
        Map observations for each csr entity
        :param subject_registry: Central subject registry
        :param study_registry: Study registry
        :return:
        """
        self.map_subject_registry_observations(subject_registry.individuals)
        self.map_subject_registry_observations(subject_registry.diagnoses)
        self.map_subject_registry_observations(subject_registry.biosources)
        self.map_subject_registry_observations(subject_registry.biomaterials, subject_registry.biosources)
        self.map_study_registry_observations(study_registry)