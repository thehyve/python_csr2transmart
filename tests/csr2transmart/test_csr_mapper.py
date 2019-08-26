import datetime
from collections import Counter
from typing import List

from transmart_loader.transmart import ValueType, DimensionType, Observation, Modifier


def get_observations_for_modifier(observations: List[Observation], modifier: Modifier) -> List[Observation]:
    return list(filter(lambda o: o.metadata is not None and o.metadata.values.get(modifier) is not None,
                       observations))


def test_studies_mapping(mapped_data_collection):
    studies = mapped_data_collection.studies
    assert len(studies) == 1
    assert studies[0].name == 'CSR'
    assert studies[0].study_id == 'CSR'
    assert studies[0].metadata.values['Load date'] is not None


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
    assert len(patients[0].mappings) == 1
    assert patients[0].mappings[0].identifier == 'P1'
    assert patients[0].mappings[0].source == 'SUB_ID'
    assert patients[1].identifier == 'P2'
    assert patients[1].sex == 'm'
    assert len(patients[1].mappings) == 1
    assert patients[1].mappings[0].identifier == 'P2'
    assert patients[1].mappings[0].source == 'SUB_ID'


def test_concepts_mapping(mapped_data_collection):
    concepts = mapped_data_collection.concepts
    assert len(concepts) == 32
    assert len(list(filter(lambda c: c.concept_code.startswith('Individual.'), concepts))) == 12
    assert len(list(filter(lambda c: c.concept_code.startswith('Diagnosis.'), concepts))) == 6
    assert len(list(filter(lambda c: c.concept_code.startswith('Biosource.'), concepts))) == 6
    assert len(list(filter(lambda c: c.concept_code.startswith('Biomaterial.'), concepts))) == 3
    assert len(list(filter(lambda c: c.concept_code.startswith('Study.'), concepts))) == 4
    assert len(list(filter(lambda c: c.concept_code.startswith('IndividualStudy.'), concepts))) == 1


def test_modifiers_mapping(mapped_data_collection):
    modifiers = mapped_data_collection.modifiers
    assert len(modifiers) == 3
    assert list(map(lambda m: m.modifier_code, modifiers)) == [
        'Diagnosis', 'Biosource', 'Biomaterial']
    assert list(map(lambda m: m.name, modifiers)) == [
        'Diagnosis', 'Biosource', 'Biomaterial']
    assert list(map(lambda m: m.modifier_path, modifiers)) == [
        'Diagnosis', 'Biosource', 'Biomaterial']
    assert list(map(lambda m: m.value_type, modifiers)) == [
        ValueType.Categorical, ValueType.Categorical, ValueType.Categorical]


def test_dimensions_mapping(mapped_data_collection):
    dimensions = mapped_data_collection.dimensions
    assert len(dimensions) == 3
    assert list(map(lambda d: d.name, dimensions)) == ['Diagnosis', 'Biosource', 'Biomaterial']
    assert list(map(lambda d: d.modifier.name if d.modifier else None, dimensions)) == [
        'Diagnosis', 'Biosource', 'Biomaterial']
    assert list(map(lambda d: d.dimension_type, dimensions)) == [
        DimensionType.Subject, DimensionType.Subject, DimensionType.Subject]
    assert list(map(lambda d: d.sort_index, dimensions)) == [2, 3, 4]


def test_ontology_mapping(mapped_data_collection):
    ontology = mapped_data_collection.ontology
    assert len(ontology) == 1
    assert len(ontology[0].children) == 5
    assert list(map(lambda t: t.name, ontology[0].children)) == ['01. Patient information',
                                                                 '02. Diagnosis information',
                                                                 '03. Biosource information',
                                                                 '04. Biomaterial information',
                                                                 '05. Study information']
    assert len(ontology[0].children[0].children) == 5  # individual node
    assert ontology[0].children[0].children[4].name == 'Informed_consent'
    assert len(ontology[0].children[0].children[4].children) == 8  # individual.Informed_consent node
    assert len(ontology[0].children[1].children) == 6  # diagnosis node
    assert len(ontology[0].children[2].children) == 6  # biosource node
    assert len(ontology[0].children[3].children) == 3  # biomaterial node
    assert len(ontology[0].children[4].children) == 5  # study node
    # TODO test metadata


def test_observations_mapping(mapped_data_collection):
    observations = mapped_data_collection.observations
    modifiers = list(mapped_data_collection.modifiers)
    diagnosis_modifier = modifiers[0]
    biosource_modifier = modifiers[1]
    biomaterial_modifier = modifiers[2]
    patient_observations = list(filter(lambda o: o.metadata is None, observations))
    diagnosis_observations = get_observations_for_modifier(observations, diagnosis_modifier)
    biosource_observations = get_observations_for_modifier(observations, biosource_modifier)
    biomaterial_observations = get_observations_for_modifier(observations, biomaterial_modifier)

    assert len(patient_observations) == 17 + 8  # individual + individual studies
    print(list(map(lambda po: po.value.value, patient_observations)))
    assert Counter(map(lambda po: po.value.value, patient_observations)) == Counter([
        'Human', 'f', datetime.date(1993, 2, 1), 'yes', datetime.date(2017, 3, 1), 'yes', 'yes', 'yes',  # P1
        'Human', 'm', datetime.date(1994, 4, 3), 'yes', datetime.date(2017, 5, 11), datetime.date(2017, 10, 14),
        'yes', 'not applicable', 'yes',  # P2
        'STUDY1', 'STD1', 'Study 1', 'http://www.example.com',  # individual study 1
        'STUDY2', 'STD2', 'Study 2', 'http://www.example.com'])  # individual study 2

    assert len(diagnosis_observations) == 18
    assert Counter(map(lambda do: do.value.value, diagnosis_observations)) == Counter([
        'neuroblastoma', 'liver', 'chemo', 'IV', datetime.date(2016, 5, 1), 'Center 1',  # D1
        'nephroblastoma', 'kidney', 'surgery', 'III', datetime.date(2016, 7, 2), 'Center 2',  # D2
        'hepatoblastoma', 'bone marrow', 'Protocol 1', 'IV', datetime.date(2016, 11, 3), 'Center 3'])  # D3
    assert Counter(map(lambda do: do.metadata.values[diagnosis_modifier].value, diagnosis_observations)) == Counter([
        'D1', 'D1', 'D1', 'D1', 'D1', 'D1',
        'D2', 'D2', 'D2', 'D2', 'D2', 'D2',
        'D3', 'D3', 'D3', 'D3', 'D3', 'D3'])

    assert len(biosource_observations) == 21
    assert Counter(map(lambda bso: bso.value.value, biosource_observations)) == Counter([
        'Yes', 'BS1', 'medula', datetime.date(2017, 3, 12), 'ST1', 5,  # BS1
        'BS2', 'cortex', datetime.date(2017, 4, 1), 'ST2', 3,   # BS2
        'BS2', 'cortex', datetime.date(2017, 5, 14), 'ST1', 2,  # BS3
        'No', 'medula', datetime.date(2017, 6, 21), 'ST2', 1])  # BS4
    assert Counter(map(lambda bso: bso.metadata.values[biosource_modifier].value, biosource_observations)) == Counter([
        'BS1', 'BS1', 'BS1', 'BS1', 'BS1', 'BS1',
        'BS2', 'BS2', 'BS2', 'BS2', 'BS2',
        'BS3', 'BS3', 'BS3', 'BS3', 'BS3',
        'BS4', 'BS4', 'BS4', 'BS4', 'BS4'])

    assert len(biomaterial_observations) == 9
    assert Counter(map(lambda bmo: bmo.value.value, biomaterial_observations)) == Counter([
        datetime.date(2017, 10, 12), 'RNA',  # BM1
        datetime.date(2017, 11, 22), 'DNA',  # BM2
        'BM2',  datetime.date(2017, 12, 12), 'RNA',  # BM3
        datetime.date(2017, 10, 12), 'DNA'])  # BM4
    assert Counter(map(lambda bmo: bmo.metadata.values[biomaterial_modifier].value, biomaterial_observations)) ==\
        Counter(['BM1', 'BM1',
                 'BM2', 'BM2',
                 'BM3', 'BM3', 'BM3',
                 'BM4', 'BM4'])

    assert len(observations) == len(patient_observations) + len(diagnosis_observations) + len(
        biosource_observations) + len(biomaterial_observations)
