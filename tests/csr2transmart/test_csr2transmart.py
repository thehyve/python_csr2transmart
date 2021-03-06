#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the csr2transmart application.
"""
from click.testing import CliRunner
from os import path

from csr2transmart import csr2transmart


def test_transformation(tmp_path):
    target_path = tmp_path.as_posix()
    runner = CliRunner()
    output_path = target_path + '/data'
    result = runner.invoke(csr2transmart.run, [
        './test_data/input_data/CSR2TRANSMART_TEST_DATA',
        output_path,
        './test_data/input_data/config'
    ])
    assert result.exit_code == 0

    assert path.exists(output_path + '/i2b2metadata/i2b2_secure.tsv')
    assert path.exists(output_path + '/i2b2demodata/concept_dimension.tsv')
    assert path.exists(output_path + '/i2b2demodata/patient_mapping.tsv')
    assert path.exists(output_path + '/i2b2demodata/patient_dimension.tsv')
    assert path.exists(output_path + '/i2b2demodata/encounter_mapping.tsv')
    assert path.exists(output_path + '/i2b2demodata/visit_dimension.tsv')
    assert path.exists(output_path + '/i2b2demodata/study.tsv')
    assert path.exists(output_path + '/i2b2metadata/dimension_description.tsv')
