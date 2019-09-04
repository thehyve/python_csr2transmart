#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the code book reader.
"""
from collections import Counter

import pytest

from csr.csr import Individual, Diagnosis, Biosource, Biomaterial, CentralSubjectRegistry
from sources2csr.ngs_reader import NgsReaderException

from sources2csr.ngs import LibraryStrategy, NGS, AnalysisType
from sources2csr.ngs2csr import read_ngs_files, add_ngs_data


def test_valid_ngs():
    ngs_data = read_ngs_files('./test_data/input_data/CLINICAL/NGS')
    count = len(ngs_data)
    assert count == 5
    # .txt and .seg files
    assert ngs_data == {
        NGS(analysis_type=AnalysisType.WGS,
            library_strategy=LibraryStrategy.CNV,
            biosource_id='PMCBS000AAA',
            biomaterial_id='PMCBM000AAA'),
        NGS(library_strategy=LibraryStrategy.CNV, biosource_id='PMCBS000AAA', biomaterial_id='PMCBM000AAA'),
        NGS(library_strategy=LibraryStrategy.CNV, biosource_id='PMCBS000AAB', biomaterial_id='PMCBM000AAB'),
        NGS(library_strategy=LibraryStrategy.SNV, biosource_id='PMCBS000AAA', biomaterial_id='PMCBM000AAA'),
        NGS(library_strategy=LibraryStrategy.SNV, biosource_id='PMCBS000AAB', biomaterial_id='PMCBM000AAB')
    }


def test_invalid_txt():
    with pytest.raises(NgsReaderException) as excinfo:
        read_ngs_files('./test_data/input_data/CLINICAL/NGS/invalid/invalid_txt')
    assert 'Cannot read NGS data from file: pmc_invalid_all_data_by_genes.txt. ' \
           'No sample_id found in header' in str(excinfo.value)


def test_invalid_sample_id():
    with pytest.raises(NgsReaderException) as excinfo:
        read_ngs_files('./test_data/input_data/CLINICAL/NGS/invalid/invalid_sample_id')
    assert 'Invalid sample_id format found in pmc_invalid_sample_id_all_data_by_genes.txt NGS file. ' \
           'sample_id: PMCBS000AAB-PMCBM000AAB' in str(excinfo.value)


def test_invalid_seg():
    with pytest.raises(NgsReaderException) as excinfo:
        read_ngs_files('./test_data/input_data/CLINICAL/NGS/invalid/invalid_seg')
    assert 'Cannot read NGS data from file: invalid.seg. Empty data.' in str(excinfo.value)


def test_maf_invalid_header():
    with pytest.raises(NgsReaderException) as excinfo:
        read_ngs_files('./test_data/input_data/CLINICAL/NGS/invalid/invalid_maf_header')
    assert 'Invalid invalid_header.maf.gz file. No column with name Tumor_Sample_Barcode. ' \
           'Cannot read sample ids.' in str(excinfo.value)


@pytest.fixture
def registry_with_biosources_and_biomaterials() -> CentralSubjectRegistry:
    individuals = [
        Individual(individual_id='P1', birth_date='1950-05-05')
    ]
    diagnoses = [
        Diagnosis(diagnosis_id='D1', individual_id='P1', diagnosis_date='2010-03-31')
    ]
    biosources = [
        Biosource(biosource_id='PMCBS000AAA', individual_id='P1', diagnosis_id='D1'),
        Biosource(biosource_id='PMCBS000AAB', individual_id='P1', diagnosis_id='D1')
    ]
    biomaterials = [
        Biomaterial(biomaterial_id='PMCBM000AAA', src_biosource_id='PMCBS000AAA'),
        Biomaterial(biomaterial_id='PMCBM000AAB', src_biosource_id='PMCBS000AAB')
    ]

    return CentralSubjectRegistry(individuals=individuals, diagnoses=diagnoses, biosources=biosources,
                                  biomaterials=biomaterials)


def test_biomaterial_library_strategy_and_analysis_type(registry_with_biosources_and_biomaterials):
    subject_registry = add_ngs_data(registry_with_biosources_and_biomaterials, './test_data/input_data/CLINICAL/NGS')

    assert len(subject_registry.biomaterials) == 2
    assert Counter(subject_registry.biomaterials[0].library_strategy) == Counter({'CNV': 2, 'SNV': 1})
    assert set(subject_registry.biomaterials[1].library_strategy) == {'CNV', 'SNV'}
    assert subject_registry.biomaterials[0].analysis_type == ['WGS']
    assert subject_registry.biomaterials[1].analysis_type == []
