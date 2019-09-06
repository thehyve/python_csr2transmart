#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the csr2transmart application.
"""
from os import path

from csr2cbio import csr2cbio


def test_transformation(tmp_path):
    target_path = tmp_path.as_posix()
    output_path = target_path + '/data'
    csr2cbio.main('./test_data/input_data/cbio_clinical',
                  './test_data/input_data/cbio_clinical/NGS',
                  output_path,
                  './test_data/input_data/config/logging.cfg')

    assert path.exists(output_path + '/data_clinical_patient.txt')
    assert path.exists(output_path + '/meta_clinical_patient.txt')
    assert path.exists(output_path + '/data_clinical_sample.txt')
    assert path.exists(output_path + '/meta_clinical_sample.txt')
    assert path.exists(output_path + '/data_cna_continuous.txt')
    assert path.exists(output_path + '/meta_cna_continuous.txt')
    assert path.exists(output_path + '/data_cna_discrete.txt')
    assert path.exists(output_path + '/meta_cna_discrete.txt')
    assert path.exists(output_path + '/data_cna_segments.seg')
    assert path.exists(output_path + '/meta_cna_segments.txt')
    assert path.exists(output_path + '/data_mutations.maf')
    assert path.exists(output_path + '/meta_mutations.txt')
    # TODO after adding more test data:
    # assert path.exists(output_path + '/meta_study')
    # assert path.exists(output_path + '/case_list/cases_cna.txt')
    # assert path.exists(output_path + '/case_list/cases_cnaseq.txt')
    # assert path.exists(output_path + '/case_list/cases_sequenced.txt')
