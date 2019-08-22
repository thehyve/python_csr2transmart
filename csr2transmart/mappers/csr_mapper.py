import datetime
from typing import Dict, Sequence, List

from pandas import DataFrame
from transmart_loader.transmart import DataCollection, Study, TrialVisit, Patient, IdentifierMapping, StudyMetadata, \
    DimensionType, ValueType, Modifier, Dimension

from csr.csr import CentralSubjectRegistry, StudyRegistry, Individual, SubjectEntity
from csr2transmart.blueprint import Blueprint
from csr2transmart.mappers.blueprint_mapper import BlueprintMapper
from csr2transmart.mappers.observation_mapper import ObservationMapper


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
        self.dimensions: List[Dimension] = []
        self.modifier_key_to_modifier: Dict[str, Modifier] = {}

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

    def map_dimensions_and_modifiers(self):
        for index, entity_type in enumerate(SubjectEntity.__args__):
            type_name = entity_type.schema()['title']
            modifier = Modifier(type_name,
                                type_name,
                                type_name,
                                ValueType.Categorical)
            self.modifier_key_to_modifier[type_name] = modifier

            modifier_dimension = Dimension(type_name,
                                           modifier,
                                           DimensionType.Subject,
                                           index)
            self.dimensions.append(modifier_dimension)

    def map(self,
            subject_registry: CentralSubjectRegistry,
            study_registry: StudyRegistry,
            blueprint: Blueprint) -> DataCollection:
        self.map_patients(subject_registry.individuals)
        study = self.map_study()
        default_trial_visit = self.map_default_trial_visit(study)

        bp_mapper = BlueprintMapper(self.individual_id_to_patient, self.top_tree_node)
        bp_mapper.map(blueprint)

        observation_mapper = ObservationMapper(default_trial_visit,
                                               self.individual_id_to_patient,
                                               bp_mapper.concept_key_to_concept,
                                               bp_mapper.concept_key_to_modifier_key,
                                               bp_mapper.modifier_key_to_modifier)
        observation_mapper.map_observations(subject_registry, study_registry)

        return DataCollection(bp_mapper.concept_key_to_concept.values(),
                              bp_mapper.modifier_key_to_modifier.values(),
                              bp_mapper.dimensions,
                              [study],
                              [default_trial_visit],
                              [],
                              bp_mapper.ontology,
                              self.individual_id_to_patient.values(),
                              observation_mapper.observations,
                              [],
                              [])
