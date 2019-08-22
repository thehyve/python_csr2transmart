#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the code book reader.
"""
import pytest

from sources2csr.codebook_mapper import read_codebook, CodeBookMapperException, CodeBookMapper


def test_valid_codebook():
    codebook = read_codebook('./test_data/input_data/codebooks/valid_codebook.txt')
    assert codebook is not None
    assert set(codebook.column_mappings.keys()) == {'consent', 'gender'}
    assert codebook.column_mappings['gender'].value_mapping == {'m': 'male', 'f': 'female', 'u': 'unknown'}


def test_invalid_codebook():
    with pytest.raises(CodeBookMapperException) as excinfo:
        read_codebook('./test_data/input_data/codebooks/invalid_codebook.txt')
    assert 'Invalid value mapping in codebook' in str(excinfo.value)


def test_invalid_header():
    with pytest.raises(CodeBookMapperException) as excinfo:
        read_codebook('./test_data/input_data/codebooks/invalid_header.txt')
    assert 'Invalid header in codebook' in str(excinfo.value)


def test_apply_codebook():
    codebook_mapper = CodeBookMapper('./test_data/input_data/codebooks/valid_codebook.txt')
    result = codebook_mapper.apply([
        {'id': 1, 'gender': 'm'},
        {'id': 2, 'gender': 'f'},
        {'id': 3, 'gender': 'u'},
        {'id': 4, 'gender': 'x'}
    ])
    assert result == [
        {'id': 1, 'gender': 'male'},
        {'id': 2, 'gender': 'female'},
        {'id': 3, 'gender': 'unknown'},
        {'id': 4, 'gender': 'x'}
    ]
