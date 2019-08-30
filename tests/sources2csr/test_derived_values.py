#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the derived diagnosis aggregates.
"""
from collections import Counter

import pytest
from csr.csr import CentralSubjectRegistry, Individual, Diagnosis, Biosource, Biomaterial

from sources2csr.helper_variables import add_derived_values, add_ngs_data
from sources2csr.ngs import NGS, LibraryStrategy, AnalysisType


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


@pytest.fixture
def registry_with_biosources_and_biomaterials() -> CentralSubjectRegistry:
    individuals = [
        Individual(individual_id='P1', birth_date='1950-05-05')
    ]
    diagnoses = [
        Diagnosis(diagnosis_id='D1', individual_id='P1', diagnosis_date='2010-03-31')
    ]
    biosources = [
        Biosource(biosource_id='BS1', individual_id='P1', diagnosis_id='D1')
    ]
    biomaterials = [
        Biomaterial(biomaterial_id='BM1', src_biosource_id='BS1'),
        Biomaterial(biomaterial_id='BM2', src_biosource_id='BS1')
    ]

    return CentralSubjectRegistry(individuals=individuals, diagnoses=diagnoses, biosources=biosources,
                                  biomaterials=biomaterials)


def test_biomaterial_library_strategy_and_analysis_type(registry_with_biosources_and_biomaterials):
    ngs_data = [
        NGS(biosource_id='BS1', biomaterial_id='BM1', library_strategy=LibraryStrategy.CNV),
        NGS(biosource_id='BS1', biomaterial_id='BM1', library_strategy=LibraryStrategy.CNV),
        NGS(biosource_id='BS1', biomaterial_id='BM1', library_strategy=LibraryStrategy.SNV),
        NGS(biosource_id='BS1', biomaterial_id='BM2', library_strategy=LibraryStrategy.CNV,
            analysis_type=AnalysisType.WGS),
        NGS(biosource_id='BS2', biomaterial_id='BM2', library_strategy=LibraryStrategy.CNV,
            analysis_type=AnalysisType.WXS),
    ]
    subject_registry = add_ngs_data(registry_with_biosources_and_biomaterials, set(ngs_data))

    assert len(subject_registry.biomaterials) == 2
    assert Counter(subject_registry.biomaterials[0].library_strategy) == Counter(['CNV', 'SNV'])
    assert subject_registry.biomaterials[1].library_strategy == ['CNV']
    assert subject_registry.biomaterials[0].analysis_type == []
    assert subject_registry.biomaterials[1].analysis_type == ['WGS']
