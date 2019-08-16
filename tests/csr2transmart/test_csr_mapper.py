import datetime
import json
import os
from typing import Dict, List

import pandas as pd
from transmart_loader.transmart import DataCollection, ValueType, DimensionType, Modifier, Observation

from csr.csr import CentralSubjectRegistry, StudyRegistry
from csr.utils import read_subject_registry_from_tsv, read_study_registry_from_tsv
from csr2transmart.blueprint import Blueprint, BlueprintElement
from csr2transmart.csr_mapper import CsrMapper


def get_observations_for_modifier(observations: List[Observation], modifier: Modifier) -> List[Observation]:
    return list(filter(lambda o: o.metadata is not None and o.metadata.values.get(modifier) is not None,
                       observations))


class TestCsrMapper:
    collection = None

    def setup(self):
        input_dir = './test_data/input_data/CSR2TRANSMART_TEST_DATA'
        config_dir = './test_data/input_data/config'
        study_id = 'CSR'
        top_tree_node = '\\Central Subject Registry\\'
        modifier_file = os.path.join(config_dir, 'modifiers.txt')
        blueprint_file = os.path.join(config_dir, 'blueprint.json')
        with open(blueprint_file, 'r') as bpf:
            bp: Dict = json.load(bpf)
        blueprint: Blueprint = {k: BlueprintElement(**v) for k, v in bp.items()}
        modifiers = pd.read_csv(modifier_file, sep='\t')

        subject_registry: CentralSubjectRegistry = read_subject_registry_from_tsv(input_dir)
        study_registry: StudyRegistry = read_study_registry_from_tsv(input_dir)

        mapper = CsrMapper(study_id, top_tree_node)
        self.collection: DataCollection = mapper.map(subject_registry, study_registry, modifiers, blueprint)

    def test_studies_mapping(self):
        studies = self.collection.studies
        assert len(studies) == 1
        assert studies[0].name == 'CSR'
        assert studies[0].study_id == 'CSR'
        assert studies[0].metadata.values['Load date'] is not None

    def test_trial_visits_mapping(self):
        trial_visits = self.collection.trial_visits
        assert len(trial_visits) == 1
        assert trial_visits[0].study.name == 'CSR'
        assert trial_visits[0].rel_time_unit is None
        assert trial_visits[0].rel_time_label == 'GENERAL'
        assert trial_visits[0].rel_time is None

    def test_patients_mapping(self):
        patients = list(self.collection.patients)
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

    def test_concepts_mapping(self):
        concepts = self.collection.concepts
        assert len(concepts) > 0
        # assert len(concepts) == 27 TODO fix after blueprint format change

    def test_modifiers_mapping(self):
        modifiers = self.collection.modifiers
        assert len(modifiers) == 3
        assert list(map(lambda m: m.modifier_code, modifiers)) == [
            'CSR_DIAGNOSIS_MOD', 'CSR_BIOSOURCE_MOD', 'CSR_BIOMATERIAL_MOD']
        assert list(map(lambda m: m.name, modifiers)) == [
            'Diagnosis ID', 'Biosource ID', 'Biomaterial ID']
        assert list(map(lambda m: m.modifier_path, modifiers)) == [
            '\\diagnose_mod', '\\biosource_mod', '\\biomaterial_mod']
        assert list(map(lambda m: m.value_type, modifiers)) == [
            ValueType.Categorical, ValueType.Categorical, ValueType.Categorical]

    def test_dimensions_mapping(self):
        dimensions = self.collection.dimensions
        assert len(dimensions) == 3
        assert list(map(lambda d: d.name, dimensions)) == ['Diagnosis ID', 'Biosource ID', 'Biomaterial ID']
        assert list(map(lambda d: d.modifier.name if d.modifier else None, dimensions)) == [
            'Diagnosis ID', 'Biosource ID', 'Biomaterial ID']
        assert list(map(lambda d: d.dimension_type, dimensions)) == [
            DimensionType.Subject, DimensionType.Subject, DimensionType.Subject]
        assert list(map(lambda d: d.sort_index, dimensions)) == [2, 3, 4]

    def test_ontology_mapping(self):
        ontology = self.collection.ontology
        assert len(ontology) == 1
        # assert len(list(map(lambda t: t.name, ontology[0].children))) == 5 TODO fix after blueprint format change

    def test_observations_mapping(self):
        observations = self.collection.observations
        modifiers = list(self.collection.modifiers)
        diagnosis_modifier = modifiers[0]
        biosource_modifier = modifiers[1]
        biomaterial_modifier = modifiers[2]
        patient_observations = list(filter(lambda o: o.metadata is None, observations))
        diagnosis_observations = get_observations_for_modifier(observations, diagnosis_modifier)
        biosource_observations = get_observations_for_modifier(observations, biosource_modifier)
        biomaterial_observations = get_observations_for_modifier(observations, biomaterial_modifier)

        assert len(patient_observations) == 17 + 8  # individual + individual studies
        assert list(map(lambda po: po.value.value, patient_observations)) == [
            'Human', 'f', datetime.date(1993, 2, 1), 'yes', datetime.date(2017, 3, 1), 'yes', 'yes', 'yes',  # P1
            'Human', 'm', datetime.date(1994, 4, 3), 'yes', datetime.date(2017, 5, 11), datetime.date(2017, 10, 14),
            'yes', 'not applicable', 'yes',  # P2
            'STUDY1', 'STD1', 'Study 1', 'http://www.example.com',  # individual study 1
            'STUDY2', 'STD2', 'Study 2', 'http://www.example.com']  # individual study 2

        assert len(diagnosis_observations) == 18
        assert list(map(lambda do: do.value.value, diagnosis_observations)) == [
            'neuroblastoma', 'liver', 'chemo', 'IV', datetime.date(2016, 5, 1), 'Center 1',  # D1
            'nephroblastoma', 'kidney', 'surgery', 'III', datetime.date(2016, 7, 2), 'Center 2',  # D2
            'hepatoblastoma', 'bone marrow', 'Protocol 1', 'IV', datetime.date(2016, 11, 3), 'Center 3']  # D3
        assert list(map(lambda do: do.metadata.values[diagnosis_modifier].value, diagnosis_observations)) == [
            'D1', 'D1', 'D1', 'D1', 'D1', 'D1',
            'D2', 'D2', 'D2', 'D2', 'D2', 'D2',
            'D3', 'D3', 'D3', 'D3', 'D3', 'D3']

        assert len(biosource_observations) == 21 + 4  # TODO fix after blueprint format change (-4)
        assert list(map(lambda bso: bso.value.value, biosource_observations)) == [
            'Yes', 'BS1', 'medula', datetime.date(2017, 3, 12), 'ST1', 5,  # BS1
            'BS2', 'cortex', datetime.date(2017, 4, 1), 'ST2', 3,  # BS2
            'BS2', 'cortex', datetime.date(2017, 5, 14), 'ST1', 2,  # BS3
            'No', 'medula', datetime.date(2017, 6, 21), 'ST2', 1,   # BS4
            'BS1', 'BS2', 'BS3', 'BS4']  # Additional 4 from biomaterials TODO fix after blueprint format change
        assert list(map(lambda bso: bso.metadata.values[biosource_modifier].value, biosource_observations)) == [
            'BS1', 'BS1', 'BS1', 'BS1', 'BS1', 'BS1',
            'BS2', 'BS2', 'BS2', 'BS2', 'BS2',
            'BS3', 'BS3', 'BS3', 'BS3', 'BS3',
            'BS4', 'BS4', 'BS4', 'BS4', 'BS4',
            'BM1', 'BM2', 'BM3', 'BM4']  # Additional 4 from biomaterials TODO fix after blueprint format change

        assert len(biomaterial_observations) == 9
        assert list(map(lambda bmo: bmo.value.value, biomaterial_observations)) == [
            datetime.date(2017, 10, 12), 'RNA',  # BM1
            datetime.date(2017, 11, 22), 'DNA',  # BM2
            'BM2',  datetime.date(2017, 12, 12), 'RNA',  # BM3
            datetime.date(2017, 10, 12), 'DNA']  # BM4
        assert list(map(lambda bmo: bmo.metadata.values[biomaterial_modifier].value, biomaterial_observations)) == [
            'BM1', 'BM1',
            'BM2', 'BM2',
            'BM3', 'BM3', 'BM3',
            'BM4', 'BM4']

        assert len(observations) == len(patient_observations) + len(diagnosis_observations) + len(
            biosource_observations) + len(biomaterial_observations)
