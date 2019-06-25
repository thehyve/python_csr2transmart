from csr2transmart.csr_transformations import csr_transformation
from csr2transmart.transmart_transformation import transmart_transformation, transform
from os import path, listdir


def test_that_transformation_finishes_successfully(tmp_path):
    test_dir = tmp_path.as_posix()
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
        path.join(test_dir, 'csr_transformation_data.tsv'),
        path.join(test_dir, 'study_registry.tsv'),
        test_dir,
        './test_data/input_data/config',
        'blueprint.json',
        'modifiers.txt',
        'CSR',
        '\\Public Studies\\CSR\\',
        False,
        None
    )
    assert set(listdir(test_dir)) == {
        'study_registry.tsv',
        'i2b2demodata',
        'i2b2metadata',
        'csr_transformation_data.tsv'
    }
