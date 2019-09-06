#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the csr2transmart application.
"""
from os import path

from scripts.cbioportal_transformation import cbio_wrapper


def test_transformation(tmp_path):
    target_path = tmp_path.as_posix()
    output_path = target_path + '/data'
    cbio_wrapper.main('./test_data/default_data',
                      './test_data/alternative_data/NGS',
                      output_path,
                      './test_data/config/cbioportal_header_descriptions.json',
                      './logging.cfg')

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
    # assert path.exists(output_path + '/meta_study')
    # assert path.exists(output_path + '/case_list/cases_cna.txt')
    # assert path.exists(output_path + '/case_list/cases_cnaseq.txt')
    # assert path.exists(output_path + '/case_list/cases_sequenced.txt')
