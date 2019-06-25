import logging
import os
import pandas as pd
import pytest
from csr2transmart.csr_read_data import validate_source_file

from csr2transmart.csr_transformations import csr_transformation, read_dict_from_file, get_overlapping_columns, \
    check_column_prio

test_data_dir = 'test_data/input_data'
default_data = os.path.join(test_data_dir, 'CLINICAL')
dummy_test_data = 'test_data/dummy_data'
missing_diag_data = 'test_data/missing_diagnosis_date'
test_config = os.path.join(test_data_dir, 'test_config')
config = os.path.join(test_data_dir, 'config')


def test_csr_transformation(tmp_path):
    # given
    output_dir = tmp_path.as_posix()
    output_filename = 'csr_transformation_data.tsv'
    output_study_filename = 'study_registry.tsv'

    # when
    csr_transformation(
        input_dir=default_data,
        output_dir=output_dir,

        config_dir=config,
        data_model='data_model.json',
        column_priority='column_priority.json',
        file_headers='file_headers.json',
        columns_to_csr='columns_to_csr.json',

        output_filename=output_filename,
        output_study_filename=output_study_filename
    )

    # then
    output_filename_path = os.path.join(output_dir, output_filename)
    assert os.path.exists(output_filename_path)
    output_study_filename_path = os.path.join(output_dir, output_study_filename)
    assert os.path.exists(output_study_filename_path)


def test_calculate_age_at_diagnosis(tmp_path):
    """Test that the CSR pipeline correctly handles missing first diagnosis date data
    by comparing the resulting csr_transformation_data.tsv file with the expected output."""
    # given
    output_dir = tmp_path.as_posix()
    output_filename = 'csr_transformation_data.tsv'
    output_study_filename = 'study_registry.tsv'

    # when
    csr_transformation(
        input_dir=missing_diag_data,
        output_dir=output_dir,

        config_dir=config,
        data_model='data_model.json',
        column_priority='column_priority.json',
        file_headers='file_headers.json',
        columns_to_csr='columns_to_csr.json',

        output_filename=output_filename,
        output_study_filename=output_study_filename
    )

    # then
    reference_df_path = os.path.join(output_dir, 'csr_transformation_data.tsv')
    reference_df = pd.read_csv(reference_df_path, sep='\t')
    reference_df = reference_df.reindex(sorted(reference_df.columns), axis=1)

    csr_output_path = os.path.join(output_dir, output_filename)
    csr_df = pd.read_csv(csr_output_path, sep='\t')
    csr_df = csr_df.reindex(sorted(csr_df.columns), axis=1)
    assert reference_df.equals(csr_df)


def test_validate_source_file():
    source_file = os.path.join(default_data, 'study.tsv')
    file_prop_dict = read_dict_from_file('file_headers.json', config)
    value = validate_source_file(file_prop_dict, source_file, 'file_headers.json')
    assert not value


def test_validate_empty_source_file():
    source_file = os.path.join(dummy_test_data, 'empty_file.txt')
    file_prop_dict = read_dict_from_file('file_headers.json', config)
    value = validate_source_file(file_prop_dict, source_file, 'file_headers.json')
    assert value


def test_get_overlapping_columns():
    file_prop_dict = read_dict_from_file('file_headers.json', config)
    header_map = read_dict_from_file('columns_to_csr.json', config)
    overlap = get_overlapping_columns(file_prop_dict, header_map)

    assert 'SRC_BIOSOURCE_ID' in overlap.keys()
    assert sorted(overlap['SRC_BIOSOURCE_ID']) == sorted(['biomaterial.tsv', 'biosource.tsv'])


def test_col_prio_triggers_unknown_prio_col_warning(caplog):
    """Test that provided priority for a column not present in the data triggers a warning."""
    check_column_prio(column_prio_dict={'COL2': ['FILE_A', 'FILE_B']},
                      col_file_dict={},
                      col_prio_file='cp.txt', file_headers_file='fh.txt')
    warning_logs = [l for l in caplog.records if l.levelno == logging.WARN]
    assert len(warning_logs) == 1
    assert "'COL2', but the column was not found in the expected columns" in warning_logs[0].message


def test_col_prio_triggers_unknown_file_warning(caplog):
    """Test that column priority containing more files than there are files
    that actually have that column triggers a warning."""
    # Unknown file in priority warning
    check_column_prio(column_prio_dict={'COL1': ['FILE_A', 'FILE_B']},
                      col_file_dict={'COL1': ['FILE_A']},
                      col_prio_file='cp.txt', file_headers_file='fh.txt')
    warning_logs = [l for l in caplog.records if l.levelno == logging.WARN]
    assert len(warning_logs) == 1
    assert "The following priority files are not used: ['FILE_B']" in warning_logs[0].message


def test_col_prio_triggers_absent_priority_error(caplog):
    """Test that absent column priority for a column that occurs in multiple files
    triggers an error log statement and results in SystemExit."""
    with pytest.raises(SystemExit) as cm:
        check_column_prio(column_prio_dict={},
                          col_file_dict={'COL1': ['FILE_A', 'FILE_B']},
                          col_prio_file='cp.txt', file_headers_file='fh.txt')
    warning_logs = caplog.records
    assert len(warning_logs) == 1
    assert "'COL1' column occurs in multiple data files: ['FILE_A', 'FILE_B'], but no prio" in warning_logs[0].message
    assert cm.value.code == 1


def test_col_prio_triggers_incomplete_priority_error(caplog):
    """Test that incomplete column priority for a column that occurs in more files
    than priority was provided triggers an error log statement and results in SystemExit."""
    with pytest.raises(SystemExit) as cm:
        check_column_prio(column_prio_dict={'COL1': ['FILE_A', 'FILE_B']},
                          col_file_dict={'COL1': ['FILE_A', 'FILE_B', 'FILE_C']},
                          col_prio_file='cp.txt', file_headers_file='fh.txt')
    warning_logs = caplog.records  # [l for l in caplog.records if l.levelno == logging.WARN]
    assert len(warning_logs) == 1
    assert 'Incomplete priority provided for column \'COL1\'' in warning_logs[0].message
    assert cm.value.code == 1


@pytest.mark.skip('todo')
def test_merge_entity_data_frames():
    assert False


@pytest.mark.skip('todo')
def combine_column_data():
    assert False


@pytest.mark.skip('todo')
def add_biosource_identifiers():
    assert False


@pytest.mark.skip('todo')
def test_build_csr_dataframe():
    assert False


@pytest.mark.skip('todo')
def test_resolve_data_conflicts():
    assert False
