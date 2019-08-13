import json
import os
from os import path
from typing import Dict

import pandas as pd
from transmart_loader.transmart import DataCollection, ValueType, DimensionType

from csr2transmart.blueprint import Blueprint, BlueprintElement
from csr2transmart.csr_mapper import CsrMapper
from sources2csr.csr_transformations import csr_transformation


class TestCsrMapper:

    collection = None

    def setup(self):
        test_dir = './test_data'
        csr_transformation(
            './test_data/input_data/CLINICAL',
            test_dir,
            './test_data/input_data/config',
            'data_model.json',
            'column_priority.json',
            'file_headers.json',
            'columns_to_csr.json',
            'csr_transformation_data.tsv',
            'study_registry.tsv',
        )
        csr_data_file_path = path.join(test_dir, 'csr_transformation_data.tsv')
        config_dir = './test_data/input_data/config'
        study_id = 'CSR'
        top_tree_node = '\\Central Subject Registry\\'
        modifier_file = os.path.join(config_dir, 'modifiers.txt')
        blueprint_file = os.path.join(config_dir, 'blueprint.json')
        with open(blueprint_file, 'r') as bpf:
            bp: Dict = json.load(bpf)
        blueprint: Blueprint = {k: BlueprintElement(**v) for k, v in bp.items()}
        modifiers = pd.read_csv(modifier_file, sep='\t')
        csr_df = pd.read_csv(csr_data_file_path, sep='\t')

        mapper = CsrMapper(study_id, top_tree_node)
        self.collection: DataCollection = mapper.map(csr_df, modifiers, blueprint)

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
        patients = self.collection.patients
        assert len(patients) > 0

    def test_observations_mapping(self):
        observations = self.collection.observations
        assert len(observations) > 0

    def test_concepts_mapping(self):
        concepts = self.collection.concepts
        assert len(concepts) > 0

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
