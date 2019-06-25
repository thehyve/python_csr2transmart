import os
import sys
import logging
from typing import Optional

import numpy as np
import pandas as pd


SAMPLE_ID_COLUMNS = ['BIOSOURCE_ID', 'BIOMATERIAL_ID']
SEQ_TYPE = 'LIBRARY_STRATEGY'
NGS_TYPE = 'ANALYSIS_TYPE'
NGS_DF_COLUMNS = SAMPLE_ID_COLUMNS + [SEQ_TYPE, NGS_TYPE]

logger = logging.getLogger(__name__)


def process_ngs_dir(directory) -> pd.DataFrame:
    """Process all the NGS data files to determine the NGS datatype and sequencing type. Return a dataframe with
    BIOSOURCE and BIOMATERIAL identifiers.

    All source files are merged into one pandas Dataframe. Duplicate rows are removed.

    :param directory: Path to the NGS directory
    :return: merged Dataframe with all files in the input directory
    """
    df = pd.DataFrame(columns=NGS_DF_COLUMNS)
    for filename in os.listdir(directory):
        file = os.path.join(directory, filename)
        if filename.startswith('.') or os.path.isdir(file):
            continue
        logger.debug('Parsing {} data file from {}'.format(filename, directory))
        df = df.append(parse_ngs_file(file), ignore_index=True)

    rows = df.shape[0]
    df.drop_duplicates(keep='first', inplace=True)
    logger.debug('Dropped {} duplicate rows'.format(df.shape[0]-rows))

    return df


def parse_ngs_file(filepath) -> pd.DataFrame:
    """Based on the filename determines the file type and how to process them. Accepted input formats are cBioPortal
    Copy Number Variation and Segment files and Mutation data in the Mutated Annotation Format (MAF).

    Parsing produces a two columns with sample identifiers (BIOSOURCE & BIOMATERIAL IDs), one column with the datatype,
    either SNV or CNV and one column with Sequencing type, either Whole genome or Whole Exome. Data- and Sequencetype
    are determined by file name.

    :param filepath: Path to the file to process including the filename
    :return:  pandas Dataframe with BIOSOURCE_ID, BIOMATERIAL_ID, SEQUENCING_TYPE and NGS_TYPE columns for input file
    """
    filename = os.path.basename(filepath)
    if filename.endswith('maf.gz'):
        df = parse_maf_file(filepath)
        df[SEQ_TYPE] = determine_sequencing_type(filename)
        df[NGS_TYPE] = 'SNV'
    elif filename.endswith('seg'):
        df = parse_seg_file(filepath)
        df[SEQ_TYPE] = determine_sequencing_type(filename)
        df[NGS_TYPE] = 'CNV'
    elif filename.endswith('_all_data_by_genes.txt') or filename.endswith('_all_thresholded.by_genes.txt'):
        df = parse_ngs_txt_file(filepath)
        df[SEQ_TYPE] = determine_sequencing_type(filename)
        df[NGS_TYPE] = 'CNV'
    else:
        logger.warning('Warning! {!r} not recognized as expected input format, skipping'.format(filename))
        df = pd.DataFrame(columns=NGS_DF_COLUMNS)

    return df


def parse_seg_file(filepath, sep='\t') -> pd.DataFrame:
    """Takes a cBioPortal CNV segment files as input and parses the first column for sample IDs. Returns a
    pandas DataFrame with two columns with a unique list of sample IDs split by '_'.

    :param filepath: filepath of cBioPortal CNV segment value files
    :param sep: separator used in files, default tab-separated
    :return: pd.DataFrame with two columns
    """
    tumor_samples = np.unique(get_data_column_from_file(filepath, column=0, sep=sep))

    df = pd.DataFrame([split_sample_ids(id_) for id_ in tumor_samples], columns=SAMPLE_ID_COLUMNS)
    if df.shape[0] != tumor_samples.size:
        logger.error('ERROR! not all tumor samples found after splitting to biosource and biomaterial, exiting')
        sys.exit(1)
    return df


def parse_ngs_txt_file(filepath, sep='\t') -> pd.DataFrame:
    """Takes a cBioPortal CNV file as input and parses the column headers for sample IDs. Returns a pandas DataFrame
    with two columns with a unique list of sample IDs split by '_'.

    Assumes that the IDs will start with 'PMC'.

    :param filepath: filepath of cBioPortal CNV discrete value files
    :param sep: separator used in files, default tab-separated
    :return: pd.DataFrame with two columns
    """
    columns = pd.read_csv(filepath, sep=sep, nrows=0, comment='#').columns
    df = pd.DataFrame(
        [split_sample_ids(column) for column in columns if column.startswith('PMC')],
        columns=SAMPLE_ID_COLUMNS
    )

    if df.shape[0] != columns.str.startswith('PMC').sum():
        logger.error('ERROR! not all tumor samples found after splitting to biosource and biomaterial, exiting')
        sys.exit(1)

    return df


def parse_maf_file(filepath, sep='\t') -> pd.DataFrame:
    """Retrieve list of sample ids from specified filepath in the Tumor_Sample_Barcode column. Returns a
    pandas DataFrame with two columns with a unique list of sample ids split by '_'.

    Expects a Mutation Annotation Format (MAF) file as input.

    :param filepath: filepath to a MAF file
    :param sep: separator used in the MAF file, default tab-separated
    :return: pandas DataFrame with BIOSOURCE and BIOMATERIAL (SAMPLE_ID_COLUMNS)
    """
    tumor_samples = np.unique(
        get_data_column_from_file(filepath, column='Tumor_Sample_Barcode', sep=sep)
    )

    df = pd.DataFrame([split_sample_ids(id_) for id_ in tumor_samples], columns=SAMPLE_ID_COLUMNS)
    if df.shape[0] != tumor_samples.size:
        logger.error('ERROR! not all tumor samples found after splitting to biosource and biomaterial, exiting')
        sys.exit(1)

    return df


def get_data_column_from_file(filepath, column, sep='\t') -> np.array:
    """Retrieve data for one column from a file.

    :params filepath: Filepath to file to retrieve the column from
    :params column_name: Column name of column to extract
    :params sep: Character used as delimiter, default '\t'
    :return: NumPy array with data from specified column
    """
    if not isinstance(column, (int, float)):
        file_header = np.genfromtxt(filepath, delimiter=sep, max_rows=1, comments='#', dtype=object)
        column_index = np.nonzero(file_header == bytes(column, encoding='utf-8'))[0][0]
    else:
        column_index = column
    column_data = np.loadtxt(filepath, delimiter=sep, dtype=object, usecols=(column_index,))

    return column_data[1:]


def split_sample_ids(x, by='_') -> Optional[tuple]:
    """Split string on 'by' character. Assumes only two values as result of split.

    :param x: String value to split
    :param by: Character to use for splitting, default: '_'
    :return: two values, first and second element of the splitted string
    """
    x_s = x.split(by)
    if len(x_s) != 2:
        logger.error('ERROR, expect sample id {!r} to return 2 items when split by {!r}, but found {} items, {}'
                     .format(x, by, len(x_s), x_s))
        return
    else:
        return x_s[0], x_s[1]


def determine_sequencing_type(filename):
    """Use filename to determine whole genome or whole exome sequencing.
    If _WGS or _WXS are not in the filename returns np.nan

    :param filename: String value, name of the file
    :return: Type of sequencing event as string, default pd.np.nan
    """
    if '_WGS' in filename.upper():
        return 'WGS'
    elif '_WXS' in filename.upper():
        return 'WXS'
    else:
        return pd.np.nan
