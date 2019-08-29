#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the code book reader.
"""
import pytest
from sources2csr.ngs_maf_reader import GzipMafReaderException

from sources2csr.ngs_reader import NgsReaderException

from sources2csr.ngs import LibraryStrategy
from sources2csr.sources_reader import read_ngs_files


def test_valid_ngs():
    ngs_list = read_ngs_files('./test_data/input_data/CLINICAL/NGS')
    assert len(ngs_list) == 4 + 2 + 4  # .txt + .seg + .maf.gz
    # .txt files
    assert ngs_list[0].analysis_type is None and ngs_list[0].library_strategy == LibraryStrategy.CNV
    assert ngs_list[0].biosource_id == 'PMCBS000AAB' and ngs_list[0].biomaterial_id == 'PMCBM000AAB'
    assert ngs_list[1].analysis_type is None and ngs_list[1].library_strategy == LibraryStrategy.CNV
    assert ngs_list[1].biosource_id == 'PMCBS000AAA' and ngs_list[1].biomaterial_id == 'PMCBM000AAA'
    assert ngs_list[2].analysis_type is None and ngs_list[2].library_strategy == LibraryStrategy.CNV
    assert ngs_list[2].biosource_id == 'PMCBS000AAB' and ngs_list[2].biomaterial_id == 'PMCBM000AAB'
    assert ngs_list[3].analysis_type is None and ngs_list[3].library_strategy == LibraryStrategy.CNV
    assert ngs_list[3].biosource_id == 'PMCBS000AAA' and ngs_list[3].biomaterial_id == 'PMCBM000AAA'

    # .seg file
    assert ngs_list[4].analysis_type is None and ngs_list[4].library_strategy == LibraryStrategy.CNV
    assert ngs_list[4].biosource_id == 'PMCBS000AAA' and ngs_list[4].biomaterial_id == 'PMCBM000AAA'
    assert ngs_list[5].analysis_type is None and ngs_list[5].library_strategy == LibraryStrategy.CNV
    assert ngs_list[5].biosource_id == 'PMCBS000AAA' and ngs_list[5].biomaterial_id == 'PMCBM000AAA'

    # .maf.gz file
    assert ngs_list[6].analysis_type is None and ngs_list[6].library_strategy == LibraryStrategy.SNV
    assert ngs_list[6].biosource_id == 'PMCBS000AAA' and ngs_list[6].biomaterial_id == 'PMCBM000AAA'
    assert ngs_list[7].analysis_type is None and ngs_list[7].library_strategy == LibraryStrategy.SNV
    assert ngs_list[7].biosource_id == 'PMCBS000AAA' and ngs_list[7].biomaterial_id == 'PMCBM000AAA'
    assert ngs_list[8].analysis_type is None and ngs_list[8].library_strategy == LibraryStrategy.SNV
    assert ngs_list[8].biosource_id == 'PMCBS000AAA' and ngs_list[8].biomaterial_id == 'PMCBM000AAA'
    assert ngs_list[9].analysis_type is None and ngs_list[9].library_strategy == LibraryStrategy.SNV
    assert ngs_list[9].biosource_id == 'PMCBS000AAB' and ngs_list[9].biomaterial_id == 'PMCBM000AAB'


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
