import json
from os import path
from typing import Sequence, Dict

import pandas as pd
import pytest
from transmart_loader.transmart import DataCollection

from csr.csr import CentralSubjectRegistry, StudyRegistry, Individual

from csr.study_registry_reader import SubjectRegistryReader
from csr.subject_registry_reader import StudyRegistryReader
from csr2transmart.blueprint import Blueprint, BlueprintElement
from csr2transmart.csr_mapper import CsrMapper


@pytest.fixture
def csr_individuals() -> Sequence[Individual]:
    return []


@pytest.fixture
def csr_subject_registry(csr_individuals) -> CentralSubjectRegistry:
    return CentralSubjectRegistry(csr_individuals, [], [], [])


@pytest.fixture
def csr_study_registry() -> StudyRegistry:
    return None


@pytest.fixture
def mapped_data_collection() -> DataCollection:
    input_dir = './test_data/input_data/CSR2TRANSMART_TEST_DATA'
    config_dir = './test_data/input_data/config'
    study_id = 'CSR'
    top_tree_node = '\\Central Subject Registry\\'
    modifier_file = path.join(config_dir, 'modifiers.txt')
    blueprint_file = path.join(config_dir, 'blueprint.json')
    with open(blueprint_file, 'r') as bpf:
        bp: Dict = json.load(bpf)
    blueprint: Blueprint = {k: BlueprintElement(**v) for k, v in bp.items()}
    modifiers = pd.read_csv(modifier_file, sep='\t')
    subject_registry_reader = SubjectRegistryReader(input_dir)
    subject_registry: CentralSubjectRegistry = subject_registry_reader.read_subject_registry()
    study_registry_reader = StudyRegistryReader(input_dir)
    study_registry: StudyRegistry = study_registry_reader.read_subject_registry()

    mapper = CsrMapper(study_id, top_tree_node)
    return mapper.map(subject_registry, study_registry, modifiers, blueprint)
