import os

import pytest

from sources2csr.csr_read_data import get_encoding, input_file_to_df, apply_header_map, determine_file_type


clinical_test_data = './test_data/input_data/CLINICAL'
dummy_test_data = './test_data/dummy_data'
test_config = './test_data/test_config'
config = './config'


@pytest.mark.skip('Unclear what this tests')
def test_apply_header_map():
    filename = 'br_test.txt'
    filepath = os.path.join(clinical_test_data, filename)
    df, _ = input_file_to_df(filepath, get_encoding(filepath), codebook=None)

    # Define header map
    header_map = {
        "br_test.txt": {
            "CIDDIAG2": "DIAGNOSIS_ID",
            "IDAABA_pseudo": "DIAGNOSIS_DATE",
            "HOSPDIAG": "CENTER_TREATMENT",
            "DIAGCD": "TUMOR_TYPE",
            "PLOCCD": "TOPOGRAPHY",
            "DIAGGRSTX": "TUMOR_STAGE",
            "IDAA_PMC": "INDIVIDUAL_ID"
        }
    }
    new_columns = apply_header_map(df.columns, header_map[filename])

    expected_columns = ['IDAA', 'CID', 'DIAGNOSIS_DATE', 'DIAGNOSIS_ID',
                        'CENTER_TREATMENT', 'TUMOR_TYPE', 'TOPOGRAPHY',
                        'TUMOR_STAGE', 'INDIVIDUAL_ID', 'TREATMENT_PROTOCOL']

    assert new_columns == expected_columns


@pytest.mark.skip('Unclear what this tests')
def test_determine_file_type():
    files = dict(
        bm_file='biomaterial.txt',
        bs_file='biosource.txt',
        idv_file='individual.txt',
        dia_file='diagnosis.txt',
        st_file='study.txt',
        ist_file='individual_study.txt'
    )
    correct_types = {
        'bm_file': 'biomaterial',
        'bs_file': 'biosource',
        'idv_file': 'individual',
        'dia_file': 'diagnosis',
        'st_file': 'study',
        'ist_file': 'individual_study'
    }

    checked_types = {}
    for key, file in files.items():
        filepath = os.path.join(dummy_test_data, file)
        df, _ = input_file_to_df(filepath, get_encoding(filepath), codebook=None)
        checked_types.update({key: determine_file_type(df.columns, file)})

    assert correct_types == checked_types
