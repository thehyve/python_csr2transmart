#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the csr2cbioportal application.
"""
from os import path

from click.testing import CliRunner

from csr2cbioportal import csr2cbioportal


def test_transformation(tmp_path):
    target_path = tmp_path.as_posix()
    output_path = target_path + '/data'
    runner = CliRunner()
    result = runner.invoke(csr2cbioportal.run, [
        './test_data/input_data/CSR2CBIOPORTAL_TEST_DATA',
        '--ngs-dir',
        './test_data/input_data/CSR2CBIOPORTAL_TEST_DATA/NGS',
        output_path
    ])
    assert result.exit_code == 0

    assert path.exists(output_path + '/data_clinical_patient.txt')
    assert path.exists(output_path + '/meta_clinical_patient.txt')
    assert path.exists(output_path + '/data_clinical_sample.txt')
    assert path.exists(output_path + '/meta_clinical_sample.txt')
    assert path.exists(output_path + '/data_cna_continuous.txt')
    assert path.exists(output_path + '/meta_cna_continuous.txt')
    assert path.exists(output_path + '/data_cna_discrete.txt')
    assert path.exists(output_path + '/meta_cna_discrete.txt')
    # TODO after fixing https://github.com/thehyve/python_csr2transmart/issues/62
#     assert path.exists(output_path + '/data_cna_segments.seg')
#     assert path.exists(output_path + '/meta_cna_segments.txt')
    assert path.exists(output_path + '/data_mutations.maf')
    assert path.exists(output_path + '/meta_mutations.txt')
    # TODO after adding more test data:
    # assert path.exists(output_path + '/meta_study')
    # assert path.exists(output_path + '/case_list/cases_cna.txt')
    # assert path.exists(output_path + '/case_list/cases_cnaseq.txt')
    # assert path.exists(output_path + '/case_list/cases_sequenced.txt')


def test_transformation_without_ngs(tmp_path):
    target_path = tmp_path.as_posix()
    output_path = target_path + '/data'
    runner = CliRunner()
    result = runner.invoke(csr2cbioportal.run, [
        './test_data/input_data/CSR2CBIOPORTAL_TEST_DATA',
        output_path
    ])
    assert result.exit_code == 0

    assert path.exists(output_path + '/data_clinical_patient.txt')
    assert path.exists(output_path + '/meta_clinical_patient.txt')
    assert path.exists(output_path + '/data_clinical_sample.txt')
    assert path.exists(output_path + '/meta_clinical_sample.txt')
    assert not path.exists(output_path + '/data_cna_continuous.txt')
    assert not path.exists(output_path + '/meta_cna_continuous.txt')
    assert not path.exists(output_path + '/data_cna_discrete.txt')
    assert not path.exists(output_path + '/meta_cna_discrete.txt')
    assert not path.exists(output_path + '/data_cna_segments.seg')
    assert not path.exists(output_path + '/meta_cna_segments.txt')
    assert not path.exists(output_path + '/data_mutations.maf')
    assert not path.exists(output_path + '/meta_mutations.txt')
