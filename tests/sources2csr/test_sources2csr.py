#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the sources2csr application.
"""
import pytest
from click.testing import CliRunner
from os import path
from pydantic import ValidationError

from csr.exceptions import DataException, ReaderException
from csr.tabular_file_reader import TabularFileReader
from sources2csr import sources2csr
from sources2csr.sources_reader import SourcesReader


def test_transformation(tmp_path):
    target_path = tmp_path.as_posix()
    runner = CliRunner()
    result = runner.invoke(sources2csr.run, [
        './test_data/input_data/CLINICAL',
        target_path,
        './test_data/input_data/config'
    ])
    assert result.exit_code == 0

    assert path.exists(target_path + '/individual.tsv')
    assert path.exists(target_path + '/diagnosis.tsv')
    assert path.exists(target_path + '/biosource.tsv')
    assert path.exists(target_path + '/biomaterial.tsv')
    assert path.exists(target_path + '/study.tsv')
    assert path.exists(target_path + '/individual_study.tsv')

    # test if codebook mapping has been applied
    individual_data = TabularFileReader(path.join(target_path, 'individual.tsv')).read_data()
    p1 = [ind for ind in individual_data if ind['individual_id'] == 'P1'][0]
    assert p1['gender'] == 'female'

    # test if derived values have been calculated, if not read from the source
    assert p1['diagnosis_count'] == '2'
    assert p1['age_first_diagnosis'] == '23'  # 01-05-2016 - 01-02-1993

    # test if aggregate values have been correctly inserted from the source
    p2 = [ind for ind in individual_data if ind['individual_id'] == 'P2'][0]
    assert p2['diagnosis_count'] == '4'
    assert p2['age_first_diagnosis'] == '50'

    # check if data from second input file is included
    p2 = [ind for ind in individual_data if ind['individual_id'] == 'P2'][0]
    assert p2['ic_withdrawn_date'] == '2018-06-02'

    # check if data from higher priority files are not overwritten
    p6 = [ind for ind in individual_data if ind['individual_id'] == 'P6'][0]
    assert p6['ic_withdrawn_date'] == '2017-10-14'

    biosource_data = TabularFileReader(path.join(target_path, 'biosource.tsv')).read_data()
    # test reading of biosources from CSV file
    bs1 = [biosource for biosource in biosource_data if biosource['biosource_id'] == 'BS1'][0]
    assert bs1['tissue'] == 'medula'
    assert bs1['biosource_date'] == '2017-03-12'
    assert bs1['tumor_percentage'] == '5'


def test_empty_identifier():
    reader = SourcesReader(
        input_dir='./test_data/input_data/CLINICAL',
        config_dir='./test_data/input_data/config/invalid_sources_config/empty_identifier')
    with pytest.raises(DataException) as excinfo:
        reader.read_subject_data()
    assert 'Empty identifier' in str(excinfo.value)


def test_duplicate_identifier():
    reader = SourcesReader(
        input_dir='./test_data/input_data/CLINICAL',
        config_dir='./test_data/input_data/config/invalid_sources_config/duplicate_identifier')
    with pytest.raises(DataException) as excinfo:
        reader.read_subject_data()
    assert 'Duplicate identifier' in str(excinfo.value)


def test_wrong_file_format():
    reader = SourcesReader(
        input_dir='./test_data/input_data/CLINICAL',
        config_dir='./test_data/input_data/config/invalid_sources_config/wrong_file_format')
    with pytest.raises(DataException) as excinfo:
        reader.read_subject_data()
    # The columns in the biosource.csv file are not correctly parsed, resulting
    # in a missing identifier column
    assert 'Identifier column \'biosource_id\' not found' in str(excinfo.value)


def test_missing_column():
    reader = SourcesReader(
        input_dir='./test_data/input_data/CLINICAL',
        config_dir='./test_data/input_data/config/invalid_sources_config/missing_column')
    with pytest.raises(DataException) as excinfo:
        reader.read_subject_data()
    assert 'Column \'tumor_type\' not found' in str(excinfo.value)


def test_non_existing_file():
    reader = SourcesReader(
        input_dir='./test_data/input_data/CLINICAL',
        config_dir='./test_data/input_data/config/invalid_sources_config/non_existing_file')
    with pytest.raises(ReaderException) as excinfo:
        reader.read_subject_data()
    assert 'File not found' in str(excinfo.value)


def test_invalid_json():
    with pytest.raises(DataException) as excinfo:
        SourcesReader(
            input_dir='./test_data/input_data/CLINICAL',
            config_dir='./test_data/input_data/config/invalid_sources_config/invalid_json')
    assert 'Error parsing source config file' in str(excinfo.value)


def test_invalid_number():
    reader = SourcesReader(
        input_dir='./test_data/input_data/CLINICAL',
        config_dir='./test_data/input_data/config/invalid_sources_config/invalid_number')
    with pytest.raises(DataException) as excinfo:
        reader.read_subject_data()
    assert 'Invalid data for Biosource with id BS6' in str(excinfo.value)


def test_invalid_date():
    reader = SourcesReader(
        input_dir='./test_data/input_data/CLINICAL',
        config_dir='./test_data/input_data/config/invalid_sources_config/invalid_date')
    with pytest.raises(DataException) as excinfo:
        reader.read_subject_data()
    assert 'Error parsing biomaterial_date from source biomaterial_with_invalid_date.tsv:biomaterial_date with id BM15'\
           in str(excinfo.value)


def test_duplicate_attributes():
    with pytest.raises(ValidationError) as excinfo:
        SourcesReader(
            input_dir='./test_data/input_data/CLINICAL',
            config_dir='./test_data/input_data/config/invalid_sources_config/duplicate_attributes')
    assert 'Duplicate attributes: taxonomy, ic_type' \
           in str(excinfo.value)


def test_biosource_cannot_be_derived_from_self():
    reader = SourcesReader(
        input_dir='./test_data/input_data/CLINICAL',
        config_dir='./test_data/input_data/config/invalid_sources_config/biosource_derived_from_self')
    with pytest.raises(DataException) as excinfo:
        reader.read_subject_data()
    assert 'Invalid data for Biosource with id BS1' in str(excinfo.value)


def test_biomaterial_cannot_be_derived_from_self():
    reader = SourcesReader(
        input_dir='./test_data/input_data/CLINICAL',
        config_dir='./test_data/input_data/config/invalid_sources_config/biomaterial_derived_from_self')
    with pytest.raises(DataException) as excinfo:
        reader.read_subject_data()
    assert 'Invalid data for Biomaterial with id BM6' in str(excinfo.value)


def test_biomaterial_type_libstrat_mismatch():
    reader = SourcesReader(
        input_dir='./test_data/input_data/CLINICAL',
        config_dir='./test_data/input_data/config/invalid_sources_config/biomaterial_type_libstrat_mismatch')
    with pytest.raises(DataException) as excinfo:
        reader.read_subject_data()
    assert 'Not allowed RNA-Seq library strategy for molecule type: DNA in line 2' in str(excinfo.value)


@pytest.mark.skip(reason="specific validation not yet implemented (TMT-1024)")
def test_diagnosis_biosource_patient_mismatch():
    """
    Individual contains P1 and P2.
    Diagnosis contains D1 linked to P2.
    Biosource contains BS1 linked to P1 and D1.
    """
    reader = SourcesReader(
        input_dir='./test_data/input_data/ind_bios_diag_mismatch_data/source_data',
        config_dir='./test_data/input_data/ind_bios_diag_mismatch_data/config')
    with pytest.raises(DataException) as excinfo:
        reader.read_subject_data()
    assert '' in str(excinfo.value)


@pytest.mark.skip(reason="specific validation not yet implemented (TMT-1025)")
def test_biomaterial_biosource_mismatch():
    """
    Biomaterial BM2 is derived form BM1,
    but originates from a different biosource.
    """
    reader = SourcesReader(
        input_dir='./test_data/input_data/bios_biom_mismatch_data/source_data',
        config_dir='./test_data/input_data/bios_biom_mismatch_data/config')
    with pytest.raises(DataException) as excinfo:
        reader.read_subject_data()
    assert '' in str(excinfo.value)
