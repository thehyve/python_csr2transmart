from typing import Dict, Sequence, List

from transmart_loader.transmart import DataCollection, Study, TrialVisit, Patient, DimensionType, ValueType, Modifier, \
    Dimension

from csr.csr import CentralSubjectRegistry, StudyRegistry, Individual, SubjectEntity, Study as CsrStudy
from csr2transmart.mappers.observation_mapper import ObservationMapper
from csr2transmart.mappers.ontology_mapper import OntologyMapper
from csr2transmart.ontology_config import TreeNode


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

    def map_study(self) -> Study:
        return Study(self.study_id, self.study_id)

    def map_default_trial_visit(self, study: Study) -> TrialVisit:
        return TrialVisit(study, self.default_trial_visit_label)

    def map_patients(self, individuals: Sequence[Individual]):
        for individual in individuals:
            patient = Patient(individual.individual_id, individual.gender, [])
            self.individual_id_to_patient[individual.individual_id] = patient

    def map_dimensions_and_modifiers(self):
        entities = list(SubjectEntity.__args__)
        entities.remove(Individual)
        entities.append(CsrStudy)
        for index, entity_type in enumerate(entities):
            type_name = entity_type.schema()['title']
            modifier = Modifier(type_name,
                                type_name,
                                type_name,
                                ValueType.Categorical)
            self.modifier_key_to_modifier[type_name] = modifier

            dimension_type = DimensionType.Attribute if entity_type is CsrStudy else DimensionType.Subject
            modifier_dimension = Dimension(type_name,
                                           modifier,
                                           dimension_type,
                                           index+2)
            self.dimensions.append(modifier_dimension)

    def map(self,
            subject_registry: CentralSubjectRegistry,
            study_registry: StudyRegistry,
            src_ontology: Sequence[TreeNode]) -> DataCollection:
        self.map_patients(subject_registry.entity_data['Individual'])
        study = self.map_study()
        default_trial_visit = self.map_default_trial_visit(study)
        self.map_dimensions_and_modifiers()

        ontology_mapper = OntologyMapper(self.top_tree_node)
        ontology = ontology_mapper.map(src_ontology)

        observation_mapper = ObservationMapper(subject_registry,
                                               study_registry,
                                               default_trial_visit,
                                               self.individual_id_to_patient,
                                               ontology_mapper.concept_code_to_concept,
                                               self.modifier_key_to_modifier)
        observation_mapper.map_observations()

        return DataCollection(ontology_mapper.concept_code_to_concept.values(),
                              self.modifier_key_to_modifier.values(),
                              self.dimensions,
                              [study],
                              [default_trial_visit],
                              [],
                              ontology,
                              self.individual_id_to_patient.values(),
                              observation_mapper.observations,
                              [],
                              [])
