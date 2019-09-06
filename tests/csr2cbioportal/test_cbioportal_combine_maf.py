import csv
import gzip
import shutil
import unittest
import tempfile
import os

from csr2cbioportal import csr2cbioportal


def create_tsv_file(file, table):
    with open(file, 'w') as tsvfile:
        writer = csv.writer(tsvfile, delimiter='\t')
        for row in table:
            writer.writerow(row)


def read_tsv_file(file):
    table = []
    with open(file, 'r') as tsvfile:
        reader = csv.reader(tsvfile, delimiter='\t')
        for row in reader:
            table.append(row)
    return table


def gz_file(file):
    result_file = file + '.gz'
    with open(file, 'rb') as f_in, gzip.open(result_file, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)


def test_basic_use_case(tmp_path):
    ngs_dir = tmp_path.as_posix()
    maf_file_1 = os.path.join(ngs_dir, 'test1.maf')
    create_tsv_file(maf_file_1, [
        ['#version 2.4'],
        ['Hugo_Symbol', 'Tumor_Sample_Barcode', 'Q', 'W'],
        ['H1', 'A', '1', '2'],
        ['H2', 'B', '3', '4']
    ])
    gz_file(maf_file_1)
    maf_file_2 = os.path.join(ngs_dir, 'test2.maf')
    create_tsv_file(maf_file_2, [
        ['#version 2.4'],
        ['Hugo_Symbol', 'Tumor_Sample_Barcode', 'W', 'Z'],
        ['H3', 'C', '5', '6'],
        ['H4', 'D', '7', '8']
    ])
    gz_file(maf_file_2)
    out_dir = tempfile.mkdtemp()
    result_maf_file = os.path.join(out_dir, 'result.maf')

    samples = csr2cbioportal.combine_maf(
        ngs_dir=ngs_dir,
        output_file_location=result_maf_file)

    assert os.path.exists(result_maf_file)
    table = read_tsv_file(result_maf_file)
    assert len(table) == 5
    assert len(table[0]) == 5
    assert 'Hugo_Symbol' in table[0]
    assert 'Tumor_Sample_Barcode' in table[0]
    assert 'Q' in table[0]
    assert 'W' in table[0]
    assert 'Z' in table[0]
    # check returned samples
    assert len(samples) == 4
    assert 'A' in samples
    assert 'B' in samples
    assert 'C' in samples
    assert 'D' in samples


def test_skip_system_file(tmp_path):
    ngs_dir = tmp_path.as_posix()
    maf_file_1 = os.path.join(ngs_dir, '.test1.maf')
    create_tsv_file(maf_file_1, [
        ['Hugo_Symbol', 'Tumor_Sample_Barcode'],
        ['H1', 'A'],
        ['H2', 'B']
    ])
    gz_file(maf_file_1)
    result_maf_file = os.path.join(ngs_dir, 'result.maf')

    samples = csr2cbioportal.combine_maf(
        ngs_dir=ngs_dir,
        output_file_location=result_maf_file)

    assert not os.path.exists(result_maf_file)
    assert len(samples) == 0


def test_skip_comment_lines(tmp_path):
    ngs_dir = tmp_path.as_posix()
    maf_file_1 = os.path.join(ngs_dir, 'test1.maf')
    create_tsv_file(maf_file_1, [
        ['Hugo_Symbol', 'Tumor_Sample_Barcode'],
        ['H1', 'A'],
        ['#H2', 'B']
    ])
    gz_file(maf_file_1)
    out_dir = tempfile.mkdtemp()
    result_maf_file = os.path.join(out_dir, 'result.maf')

    samples = csr2cbioportal.combine_maf(
        ngs_dir=ngs_dir,
        output_file_location=result_maf_file)

    assert os.path.exists(result_maf_file)
    assert len(samples) == 1
    assert 'A' in samples
