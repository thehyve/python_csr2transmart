#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the sources2csr application.
"""
from click.testing import CliRunner
from os import path

from csr.tsv_reader import TsvReader

from sources2csr import sources2csr


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
    individual_data = TsvReader(path.join(target_path, 'individual.tsv')).read_data()
    assert [ind['gender'] for ind in individual_data if ind['individual_id'] == 'P1'] == ['female']
