import pytest

from sources2csr.sources2csr import sources2csr
from csr2transmart.transmart_transformation import transform
from os import listdir


@pytest.mark.skip('Invalid data')
def test_that_transformation_finishes_successfully(tmp_path):
    test_dir = tmp_path.as_posix()
    out_dir = test_dir + '/data'
    sources2csr(
        './test_data/input_data/CLINICAL',
        test_dir,
        './test_data/input_data/config')
    transform(
        './test_data/input_data/CLINICAL',
        out_dir,
        './test_data/input_data/config',
        'CSR',
        '\\Central Subject Registry\\'
    )
    assert set(listdir(test_dir)) == {
        'study_registry.tsv',
        'data',
        'csr_transformation_data.tsv',
        'study.tsv',
        'individual.tsv',
        'individual_study.tsv',
        'diagnosis.tsv',
        'biosource.tsv',
        'biomaterial.tsv'
    }
    assert set(listdir(out_dir)) == {
        'i2b2demodata',
        'i2b2metadata'
    }
