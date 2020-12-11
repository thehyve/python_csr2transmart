#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the derived diagnosis aggregates.
"""
import pytest
from csr.csr import CentralSubjectRegistry, Individual, Diagnosis, Biosource, Biomaterial
from click.testing import CliRunner
from sources2csr import sources2csr
from csr.tabular_file_reader import TabularFileReader
from os import path
from sources2csr.derived_values import add_derived_values


@pytest.fixture
def registry_with_diagnoses() -> CentralSubjectRegistry:
    individuals = [
        Individual(individual_id='P1', birth_date='1950-05-05'),
        Individual(individual_id='P2', birth_date='2001-01-01'),
        Individual(individual_id='P3', birth_date='2001-01-01', age_first_diagnosis=5),
        Individual(individual_id='P4', birth_date='2001-01-01', diagnosis_count=3),
    ]
    diagnoses = [
        Diagnosis(diagnosis_id='D1.1', individual_id='P1', diagnosis_date='2010-03-31'),
        Diagnosis(diagnosis_id='D1.2', individual_id='P1', diagnosis_date='2012-05-05'),
        Diagnosis(diagnosis_id='D2.1', individual_id='P2', diagnosis_date='2011-12-01'),
        Diagnosis(diagnosis_id='D3.1', individual_id='P3', diagnosis_date='2011-12-01'),
        Diagnosis(diagnosis_id='D4.1', individual_id='P4', diagnosis_date='2011-12-01'),
    ]
    return CentralSubjectRegistry.create({'Individual': individuals, 'Diagnosis': diagnoses})


def test_diagnosis_aggregates(registry_with_diagnoses):
    subject_registry = add_derived_values(registry_with_diagnoses)
    expected_counts = {'P1': 2, 'P2': 1, 'P3': 1, 'P4': 3}
    expected_age = {'P1': 59, 'P2': 10, 'P3': 5, 'P4': 10}
    for individual in subject_registry.entity_data['Individual']:
        assert individual.age_first_diagnosis is not None
        assert individual.age_first_diagnosis == expected_age[individual.individual_id]
        assert individual.diagnosis_count is not None
        assert individual.diagnosis_count == expected_counts[individual.individual_id]


@pytest.fixture
def registry_with_missing_diagnosis_data() -> CentralSubjectRegistry:
    individuals = [
        Individual(individual_id='P1', birth_date='1950-05-05'),
        Individual(individual_id='P2', birth_date='2001-01-01'),
        Individual(individual_id='P3', birth_date='2002-07-07'),
        Individual(individual_id='P4')
    ]
    diagnoses = [
        Diagnosis(diagnosis_id='D1.1', individual_id='P1', diagnosis_date='2010-03-31'),
        Diagnosis(diagnosis_id='D2.1', individual_id='P2'),
        Diagnosis(diagnosis_id='D2.2', individual_id='P2'),
        Diagnosis(diagnosis_id='D4.1', individual_id='P4', diagnosis_date='2012-02-15')
    ]
    return CentralSubjectRegistry.create({'Individual': individuals, 'Diagnosis': diagnoses})


def test_diagnosis_aggregates_with_missing_data(registry_with_missing_diagnosis_data):
    subject_registry = add_derived_values(registry_with_missing_diagnosis_data)
    expected_counts = {'P1': 1, 'P2': 2, 'P3': None, 'P4': 1}
    expected_age = {'P1': 59, 'P2': None, 'P3': None, 'P4': None}
    for individual in subject_registry.entity_data['Individual']:
        assert individual.age_first_diagnosis == expected_age[individual.individual_id]
        assert individual.diagnosis_count == expected_counts[individual.individual_id]


def test_transform_with_derived_data(tmp_path):
    target_path = tmp_path.as_posix()
    runner = CliRunner()
    result = runner.invoke(sources2csr.run, [
        './test_data/input_data/CLINICAL',
        target_path,
        './test_data/input_data/config/valid_config/derived_values'
    ])

    assert result.exit_code == 0, result.output

    # test if codebook mapping has been applied
    individual_data = TabularFileReader(path.join(target_path, 'individual.tsv')).read_data()
    p1 = [ind for ind in individual_data if ind['individual_id'] == 'P1'][0]
    assert p1['gender'] == 'female'

    # test if values have been correctly inserted from the source
    assert p1['diagnosis_count'] == '4'
    assert p1['age_first_diagnosis'] == '50'

    # check if missing the value, it is still correctly calculated
    p2 = [ind for ind in individual_data if ind['individual_id'] == 'P2'][0]
    assert p2['diagnosis_count'] == '1'
    assert p2['age_first_diagnosis'] == '23'  # 01-05-2016 - 01-02-1993
