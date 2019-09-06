import csv
import gzip
import shutil
import unittest
import tempfile
import os

from csr2cbio import csr2cbio


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


class CbioCombineMafTest(unittest.TestCase):

    def test_basic_use_case(self):
        ngs_dir = tempfile.mkdtemp()
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

        samples = csr2cbio.combine_maf(
            ngs_dir=ngs_dir,
            output_file_location=result_maf_file)

        self.assertTrue(os.path.exists(result_maf_file))
        table = read_tsv_file(result_maf_file)
        self.assertEqual(5, len(table))
        self.assertEqual(5, len(table[0]))
        self.assertIn('Hugo_Symbol', table[0])
        self.assertIn('Tumor_Sample_Barcode', table[0])
        self.assertIn('Q', table[0])
        self.assertIn('W', table[0])
        self.assertIn('Z', table[0])
        # check returned samples
        self.assertEqual(4, len(samples))
        self.assertIn('A', samples)
        self.assertIn('B', samples)
        self.assertIn('C', samples)
        self.assertIn('D', samples)

    def test_skip_system_file(self):
        ngs_dir = tempfile.mkdtemp()
        maf_file_1 = os.path.join(ngs_dir, '.test1.maf')
        create_tsv_file(maf_file_1, [
            ['Hugo_Symbol', 'Tumor_Sample_Barcode'],
            ['H1', 'A'],
            ['H2', 'B']
        ])
        gz_file(maf_file_1)
        out_dir = tempfile.mkdtemp()
        result_maf_file = os.path.join(out_dir, 'result.maf')

        samples = csr2cbio.combine_maf(
            ngs_dir=ngs_dir,
            output_file_location=result_maf_file)

        self.assertFalse(os.path.exists(result_maf_file))
        self.assertEqual(0, len(samples))

    def test_skip_comment_lines(self):
        ngs_dir = tempfile.mkdtemp()
        maf_file_1 = os.path.join(ngs_dir, 'test1.maf')
        create_tsv_file(maf_file_1, [
            ['Hugo_Symbol', 'Tumor_Sample_Barcode'],
            ['H1', 'A'],
            ['#H2', 'B']
        ])
        gz_file(maf_file_1)
        out_dir = tempfile.mkdtemp()
        result_maf_file = os.path.join(out_dir, 'result.maf')

        samples = csr2cbio.combine_maf(
            ngs_dir=ngs_dir,
            output_file_location=result_maf_file)

        self.assertTrue(os.path.exists(result_maf_file))
        self.assertEqual(1, len(samples))
        self.assertIn('A', samples)


if __name__ == '__main__':
    unittest.main()
