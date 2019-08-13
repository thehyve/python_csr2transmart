from sources2csr.csr_transformations import csr_transformation
from csr2transmart.transmart_transformation import transform
from os import path, listdir


def test_that_transformation_finishes_successfully(tmp_path):
    test_dir = tmp_path.as_posix()
    out_dir = test_dir + '/data'
    csr_transformation(
        './test_data/input_data/CLINICAL',
        test_dir,
        './test_data/input_data/config',
        'data_model.json',
        'column_priority.json',
        'file_headers.json',
        'columns_to_csr.json',
        'csr_transformation_data.tsv',
        'study_registry.tsv',
    )
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
        'csr_transformation_data.tsv'
    }
    assert set(listdir(out_dir)) == {
        'i2b2demodata',
        'i2b2metadata'
    }
