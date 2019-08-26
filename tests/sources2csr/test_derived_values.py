#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the derived diagnosis aggregates.
"""
import pytest
from csr.csr import CentralSubjectRegistry, Individual, Diagnosis

from sources2csr.derived_values import add_derived_values


@pytest.fixture
def registry_with_diagnoses() -> CentralSubjectRegistry:
    individuals = [
        Individual(individual_id='P1', birth_date='1950-05-05'),
        Individual(individual_id='P2', birth_date='2001-01-01')
    ]
    diagnoses = [
        Diagnosis(diagnosis_id='D1.1', individual_id='P1', diagnosis_date='2010-03-31'),
        Diagnosis(diagnosis_id='D1.2', individual_id='P1', diagnosis_date='2012-05-05'),
        Diagnosis(diagnosis_id='D2.1', individual_id='P2', diagnosis_date='2011-12-01'),
    ]
    return CentralSubjectRegistry(individuals=individuals, diagnoses=diagnoses)


def test_diagnosis_aggregates(registry_with_diagnoses):
    subject_registry = add_derived_values(registry_with_diagnoses)
    expected_counts = {'P1': 2, 'P2': 1}
    expected_age = {'P1': 59, 'P2': 10}
    for individual in subject_registry.individuals:
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
        Diagnosis(diagnosis_id='D4.1', individual_id='P4', diagnosis_date='2012-02-15'),
    ]
    return CentralSubjectRegistry(individuals=individuals, diagnoses=diagnoses)


def test_diagnosis_aggregates_with_missing_data(registry_with_missing_diagnosis_data):
    subject_registry = add_derived_values(registry_with_missing_diagnosis_data)
    expected_counts = {'P1': 1, 'P2': 2, 'P3': None, 'P4': 1}
    expected_age = {'P1': 59, 'P2': None, 'P3': None, 'P4': None}
    for individual in subject_registry.individuals:
        assert individual.age_first_diagnosis == expected_age[individual.individual_id]
        assert individual.diagnosis_count == expected_counts[individual.individual_id]
