from typing import Sequence

import pytest
from transmart_loader.transmart import DataCollection

from csr.csr import CentralSubjectRegistry, StudyRegistry, Individual
from csr.subject_registry_reader import SubjectRegistryReader
from csr.study_registry_reader import StudyRegistryReader
from csr2transmart.csr2transmart import read_configuration
from csr2transmart.mappers.csr_mapper import CsrMapper
from csr2transmart.ontology_config import OntologyConfig


@pytest.fixture
def csr_individuals() -> Sequence[Individual]:
    return []


@pytest.fixture
def csr_subject_registry(csr_individuals) -> CentralSubjectRegistry:
    return CentralSubjectRegistry.create({'Individual': csr_individuals})


@pytest.fixture
def csr_study_registry() -> StudyRegistry:
    return None


@pytest.fixture
def mapped_data_collection() -> DataCollection:
    input_dir = './test_data/input_data/CSR2TRANSMART_TEST_DATA'
    config_dir = './test_data/input_data/config'
    study_id = 'CSR'
    top_tree_node = '\\Central Subject Registry\\'
    ontology_config: OntologyConfig = read_configuration(config_dir)
    subject_registry_reader = SubjectRegistryReader(input_dir)
    subject_registry: CentralSubjectRegistry = subject_registry_reader.read_subject_registry()
    study_registry_reader = StudyRegistryReader(input_dir)
    study_registry: StudyRegistry = study_registry_reader.read_study_registry()

    mapper = CsrMapper(study_id, top_tree_node)
    return mapper.map(subject_registry, study_registry, ontology_config.nodes)
