import datetime
from collections import Counter
from typing import List, Union

from transmart_loader.transmart import ValueType, DimensionType, Observation, Modifier


def get_observations_for_modifier(observations: List[Observation],
                                  modifier: Modifier,
                                  exclude_modifier: Union[Modifier, List[Modifier]] = None) -> List[Observation]:
    if exclude_modifier is not None and isinstance(exclude_modifier, Modifier):
        exclude_modifier = [exclude_modifier]

    return [o for o in observations if o.metadata is not None and o.metadata.values.get(modifier) is not None
            and (exclude_modifier is None or all([exclude not in o.metadata.values for exclude in exclude_modifier]))]


def test_studies_mapping(mapped_data_collection):
    studies = mapped_data_collection.studies
    assert len(studies) == 1
    assert studies[0].name == 'CSR'
    assert studies[0].study_id == 'CSR'
    assert studies[0].metadata is None


def test_trial_visits_mapping(mapped_data_collection):
    trial_visits = mapped_data_collection.trial_visits
    assert len(trial_visits) == 1
    assert trial_visits[0].study.name == 'CSR'
    assert trial_visits[0].rel_time_unit is None
    assert trial_visits[0].rel_time_label == 'GENERAL'
    assert trial_visits[0].rel_time is None


def test_patients_mapping(mapped_data_collection):
    patients = list(mapped_data_collection.patients)
    assert len(patients) == 2
    assert patients[0].identifier == 'P1'
    assert patients[0].sex == 'f'
    assert len(patients[0].mappings) == 0
    assert patients[1].identifier == 'P2'
    assert patients[1].sex == 'm'
    assert len(patients[1].mappings) == 0


def test_concepts_mapping(mapped_data_collection):
    concepts = mapped_data_collection.concepts
    assert len(concepts) == 38
    assert len([c for c in concepts if c.concept_code.startswith('Individual.')]) == 9
    assert len([c for c in concepts if c.concept_code.startswith('Diagnosis.')]) == 6
    assert len([c for c in concepts if c.concept_code.startswith('Biosource.')]) == 6
    assert len([c for c in concepts if c.concept_code.startswith('Biomaterial.')]) == 5
    assert len([c for c in concepts if c.concept_code.startswith('Study.')]) == 4
    assert len([c for c in concepts if c.concept_code.startswith('Radiology.')]) == 7
    assert len([c for c in concepts if c.concept_code.startswith('IndividualStudy.')]) == 1


def test_modifiers_mapping(mapped_data_collection):
    modifiers = mapped_data_collection.modifiers
    assert len(modifiers) == 5
    assert [m.modifier_code for m in modifiers] == ['Diagnosis', 'Biosource', 'Biomaterial', 'Radiology', 'Study']
    assert [m.name for m in modifiers] == ['Diagnosis', 'Biosource', 'Biomaterial', 'Radiology', 'Study']
    assert [m.modifier_path for m in modifiers] == ['Diagnosis', 'Biosource', 'Biomaterial', 'Radiology', 'Study']
    assert [m.value_type for m in modifiers] == [ValueType.Categorical] * 5


def test_dimensions_mapping(mapped_data_collection):
    dimensions = mapped_data_collection.dimensions
    assert len(dimensions) == 5
    assert [d.name for d in dimensions] == ['Diagnosis', 'Biosource', 'Biomaterial', 'Radiology', 'Study']
    assert [d.modifier.name for d in dimensions] == ['Diagnosis', 'Biosource', 'Biomaterial', 'Radiology', 'Study']
    assert [d.dimension_type for d in dimensions] == [DimensionType.Subject] * 4 + [DimensionType.Attribute]
    assert [d.sort_index for d in dimensions] == [2, 3, 4, 5, 6]


def test_ontology_mapping(mapped_data_collection):
    ontology = mapped_data_collection.ontology
    assert len(ontology) == 1
    date = datetime.datetime.now().strftime('%d-%m-%Y')
    assert ontology[0].metadata.values['Load date'] == date
    assert ontology[0].name == 'Central Subject Registry'
    assert len(ontology[0].children) == 6
    assert [t.name for t in ontology[0].children] == ['01. Patient information',
                                                      '02. Diagnosis information',
                                                      '03. Biosource information',
                                                      '04. Biomaterial information',
                                                      '05. Study information',
                                                      '06. Radiology information']
    assert len(ontology[0].children[0].children) == 5  # individual node
    assert ontology[0].children[0].children[4].name == 'Informed_consent'
    assert len(ontology[0].children[0].children[4].children) == 5  # individual.Informed_consent node
    assert len(ontology[0].children[1].children) == 6  # diagnosis node
    assert len(ontology[0].children[2].children) == 6  # biosource node
    assert len(ontology[0].children[3].children) == 5  # biomaterial node
    assert len(ontology[0].children[4].children) == 5  # study node
    assert len(ontology[0].children[5].children) == 7  # radiology node

    assert ontology[0].children[0].children[0].concept.concept_code == 'Individual.gender'
    assert ontology[0].children[0].children[0].metadata.values['subject_dimension'] == 'patient'
    assert ontology[0].children[1].children[0].concept.concept_code == 'Diagnosis.tumor_type'
    assert ontology[0].children[1].children[0].metadata.values['subject_dimension'] == 'Diagnosis'
    assert ontology[0].children[2].children[0].concept.concept_code == 'Biosource.biosource_dedicated'
    assert ontology[0].children[2].children[0].concept.concept_code == 'Biosource.biosource_status'
    assert ontology[0].children[2].children[0].metadata.values['subject_dimension'] == 'Biosource'
    assert ontology[0].children[3].children[0].concept.concept_code == 'Biomaterial.src_biomaterial_id'
    assert ontology[0].children[3].children[0].metadata.values['subject_dimension'] == 'Biomaterial'
    assert ontology[0].children[4].children[0].concept.concept_code == 'Study.study_id'
    assert ontology[0].children[4].children[0].metadata is None
    assert ontology[0].children[5].children[0].concept.concept_code == 'Radiology.radiology_id'


def test_observations_mapping(mapped_data_collection):
    observations = mapped_data_collection.observations
    modifiers = list(mapped_data_collection.modifiers)
    diagnosis_modifier: Modifier = modifiers[0]
    assert diagnosis_modifier.name == 'Diagnosis'
    biosource_modifier: Modifier = modifiers[1]
    assert biosource_modifier.name == 'Biosource'
    biomaterial_modifier: Modifier = modifiers[2]
    assert biomaterial_modifier.name == 'Biomaterial'
    radiology_modifier: Modifier = modifiers[3]
    assert radiology_modifier.name == 'Radiology'
    study_modifier: Modifier = modifiers[4]
    assert study_modifier.name == 'Study'
    patient_observations = [o for o in observations if o.metadata is None]
    diagnosis_observations = get_observations_for_modifier(observations, diagnosis_modifier, [biosource_modifier,
                                                                                              radiology_modifier])
    biosource_observations = get_observations_for_modifier(observations, biosource_modifier, biomaterial_modifier)
    biomaterial_observations = get_observations_for_modifier(observations, biomaterial_modifier)
    radiology_observations = get_observations_for_modifier(observations, radiology_modifier)
    study_observations = get_observations_for_modifier(observations, study_modifier)

    assert len(patient_observations) == 13
    assert Counter([po.value.value for po in patient_observations]) == Counter([
        'Human', 'f', datetime.date(1993, 2, 1), 'yes', datetime.date(2017, 3, 1), 'yes',  # P1
        'Human', 'm', datetime.date(1994, 4, 3), 'yes', datetime.date(2017, 5, 11), datetime.date(2017, 10, 14),
        'yes',  # P2
    ])
    assert len(study_observations) == 8 + 2  # studies + individual studies
    assert Counter([so.value.value for so in study_observations]) == Counter([
        'STUDY1', 'STD1', 'Study 1', 'http://www.example.com',   # study 1
        'STUDY2', 'STD2', 'Study 2', 'http://www.example.com',   # study 2
        '1', '2'
    ])  # individual studies

    assert len(radiology_observations) == 19
    assert Counter([ro.value.value for ro in radiology_observations]) == Counter([
        "R1", datetime.date(2016, 5, 1), "type_2", "P1", "D1", "torso",
        "R2", datetime.date(2016, 7, 2), "type_2", "50", "P2", "D2", "torso",
        "R3", datetime.date(2016, 11, 3), "type_1", "20", "P2", "legs"
    ])

    assert len(diagnosis_observations) == 18
    assert Counter([do.value.value for do in diagnosis_observations]) == Counter([
        'neuroblastoma', 'liver', 'chemo', 'IV', datetime.date(2016, 5, 1), 'Center 1',                 # D1
        'nephroblastoma', 'kidney', 'surgery', 'III', datetime.date(2016, 7, 2), 'Center 2',            # D2
        'hepatoblastoma', 'bone marrow', 'Protocol 1', 'IV', datetime.date(2016, 11, 3), 'Center 3'])   # D3
    assert Counter([do.metadata.values[diagnosis_modifier].value for do in diagnosis_observations]) == Counter(
        ['D1'] * 6 + ['D2'] * 6 + ['D3'] * 6)

    assert len(biosource_observations) == 19
    assert Counter([bso.value.value for bso in biosource_observations]) == Counter([
        'Yes', 'medula', datetime.date(2017, 3, 12), 'ST1', 5,  # BS1
        'cortex', datetime.date(2017, 4, 1), 'ST2', 3,   # BS2
        'BS2', 'cortex', datetime.date(2017, 5, 14), 'ST1', 2,  # BS3
        'No', 'medula', datetime.date(2017, 6, 21), 'ST2', 1])  # BS4
    assert Counter([bso.metadata.values[biosource_modifier].value for bso in biosource_observations]) == Counter([
        'BS1', 'BS1', 'BS1', 'BS1', 'BS1',
        'BS2', 'BS2', 'BS2', 'BS2',
        'BS3', 'BS3', 'BS3', 'BS3', 'BS3',
        'BS4', 'BS4', 'BS4', 'BS4', 'BS4'])
    assert Counter([bso.metadata.values[diagnosis_modifier].value
                    for bso in biosource_observations
                    if diagnosis_modifier in bso.metadata.values]) == Counter(
        ['D1', 'D1', 'D1', 'D1', 'D1',
         'D2', 'D2', 'D2', 'D2',
         'D3', 'D3', 'D3', 'D3', 'D3'])

    assert len(biomaterial_observations) == 9
    assert Counter([bmo.value.value for bmo in biomaterial_observations]) == Counter([
        datetime.date(2017, 10, 12), 'RNA',  # BM1
        datetime.date(2017, 11, 22), 'DNA',  # BM2
        'BM2',  datetime.date(2017, 12, 12), 'RNA',  # BM3
        datetime.date(2017, 10, 12), 'DNA'])  # BM4
    assert Counter([bmo.metadata.values[biomaterial_modifier].value for bmo in biomaterial_observations]) == Counter([
        'BM1', 'BM1',
        'BM2', 'BM2',
        'BM3', 'BM3', 'BM3',
        'BM4', 'BM4'])
    assert Counter([bmo.metadata.values[biosource_modifier].value
                    for bmo in biomaterial_observations
                    if biosource_modifier in bmo.metadata.values]) == Counter(
        ['BS1', 'BS1',
         'BS2', 'BS2',
         'BS3', 'BS3', 'BS3',
         'BS4', 'BS4'])
    assert Counter([bmo.metadata.values[diagnosis_modifier].value
                    for bmo in biomaterial_observations
                    if diagnosis_modifier in bmo.metadata.values]) == Counter(
        ['D1', 'D1',
         'D2', 'D2',
         'D3', 'D3'])

    assert len(observations) == len(patient_observations) + len(diagnosis_observations) + len(
        biosource_observations) + len(biomaterial_observations) + len(study_observations) + len(radiology_observations)
