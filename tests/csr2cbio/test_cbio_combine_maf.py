import unittest
import tempfile
import os
from tests.file_helpers import create_tsv_file, read_tsv_file, gz_file
from scripts.cbioportal_transformation import cbio_wrapper


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

        samples = cbio_wrapper.combine_maf(
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

        samples = cbio_wrapper.combine_maf(
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

        samples = cbio_wrapper.combine_maf(
            ngs_dir=ngs_dir,
            output_file_location=result_maf_file)

        self.assertTrue(os.path.exists(result_maf_file))
        self.assertEqual(1, len(samples))
        self.assertIn('A', samples)


if __name__ == '__main__':
    unittest.main()
