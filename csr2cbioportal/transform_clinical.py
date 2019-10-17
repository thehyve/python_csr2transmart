#!/usr/bin/env python3

# Code to transform clinical data
# Author: Sander Tan, The Hyve

import logging
import os
import re
import sys

import numpy as np
import pandas as pd

from csr.csr import CentralSubjectRegistry
from .create_metafile import create_meta_content

logger = logging.getLogger(__name__)
logger.name = logger.name.rsplit('.', 1)[1]

# Rename column headers in patient clinical data
RENAME_CLINICAL_DATA_HEADER = {'INDIVIDUAL_ID': 'PATIENT_ID'}
# Force some datatypes to be remappad to STRING
FORCE_STRING_LIST = ['CENTER_TREATMENT', 'CID', 'DIAGNOSIS_ID', 'GENDER', 'IC_DATA', 'IC_LINKING_EXT', 'IC_MATERIAL',
                     'IC_TYPE', 'INDIVIDUAL_STUDY_ID', 'TOPOGRAPHY', 'TUMOR_TYPE']


def create_clinical_header(df):
    """ Function to create header in cBioPortal format for clinical data
    """

    # Create attribute name and attribute description
    header_data = pd.DataFrame(data=df.columns)
    header_data[1] = header_data

    # Data type header line
    type_values = []
    for i in df.dtypes:
        if np.issubdtype(i, np.number):
            type_values.append('NUMBER')
        else:
            type_values.append('STRING')

    # Create attribute type and attribute priority
    header_data[2] = type_values
    header_data[3] = 1

    # Transpose to put in correct format
    header_data = header_data.transpose()

    # Transform to dataframe
    header_data = pd.DataFrame(header_data)
    header_data.columns = df.columns

    # TODO: Major - Check FORCE_STRING_LIST assumption --> make configurable?
    # Set datatype of specific columns before after header
    for string_column_name in FORCE_STRING_LIST:
        if string_column_name in header_data.columns:
            header_data.loc[2, string_column_name] = 'STRING'

    # Adding hash # to the first column
    header_data.iloc[:, 0] = '#' + header_data.iloc[:, 0].astype(str)

    return header_data


def to_sample_data(biosource_data, biomaterial_data, diagnosis_data) -> pd.DataFrame:
    """ Merge diagnoses, biosources and biomaterials into samples data frame
    """
    diagnosis_biosource_data = pd.merge(biosource_data, diagnosis_data, how='left', on=['DIAGNOSIS_ID'])
    sample_data = pd.merge(biomaterial_data, diagnosis_biosource_data, how='left',
                           left_on=['SRC_BIOSOURCE_ID'], right_on=['BIOSOURCE_ID'])
    # remove suffixes for biomaterials and biosources
    if 'SRC_BIOSOURCE_ID_x' in sample_data.columns:
        x_ = sample_data['SRC_BIOSOURCE_ID_x']
        y_ = sample_data['SRC_BIOSOURCE_ID_y']
        sample_data['SRC_BIOSOURCE_ID'] = x_.combine_first(y_)
        sample_data = sample_data.drop(columns=['SRC_BIOSOURCE_ID_x', 'SRC_BIOSOURCE_ID_y'])
    # remove suffixes for patients
    if 'PATIENT_ID_x' in sample_data.columns:
        x_ = sample_data['PATIENT_ID_x']
        y_ = sample_data['PATIENT_ID_y']
        sample_data['PATIENT_ID'] = x_.combine_first(y_)
        sample_data = sample_data.drop(columns=['PATIENT_ID_x', 'PATIENT_ID_y'])
    sample_data['SAMPLE_ID'] = sample_data['BIOSOURCE_ID'] + "_" + sample_data['BIOMATERIAL_ID']
    return sample_data


def subject_registry_to_sample_data_df(subject_registry: CentralSubjectRegistry) -> pd.DataFrame:
    diagnosis_data = pd.DataFrame.from_records([s.__dict__ for s in subject_registry.entity_data['Diagnosis']])
    biosource_data = pd.DataFrame.from_records([s.__dict__ for s in subject_registry.entity_data['Biosource']])
    biomaterial_data = pd.DataFrame.from_records([s.__dict__ for s in subject_registry.entity_data['Biomaterial']])

    diagnosis_data.columns = [x.upper() for x in diagnosis_data.columns]
    biosource_data.columns = [x.upper() for x in biosource_data.columns]
    biomaterial_data.columns = [x.upper() for x in biomaterial_data.columns]

    diagnosis_data.rename(columns=RENAME_CLINICAL_DATA_HEADER, inplace=True)
    biosource_data.rename(columns=RENAME_CLINICAL_DATA_HEADER, inplace=True)

    return to_sample_data(biosource_data, biomaterial_data, diagnosis_data)


def subject_registry_to_patient_data_df(subject_registry: CentralSubjectRegistry) -> pd.DataFrame:
    patient_data = pd.DataFrame.from_records([s.__dict__ for s in subject_registry.entity_data['Individual']])

    patient_data.columns = [x.upper() for x in patient_data.columns]
    patient_data.rename(columns=RENAME_CLINICAL_DATA_HEADER, inplace=True)

    return patient_data


def check_integer_na_columns(numerical_column):
    """ Integer columns containing NA values are converted to Float in pandas
        This function checks for a column if it only contains integers (.0)
        In this case we attempt to convert all columns, not just the columns
        that contain an NA value, because we sliced the dataframes from a bigger
        dataframe that could contain NA values.
    """
    for i in numerical_column:
        if str(i) != 'nan':
            decimal_value = str(i).split('.')[1]
            # If float is other than 0, we know for sure it's not an integer column
            if float(decimal_value) != 0:
                return False
    # If loop ends by only encountering .0, return true
    return True


def fix_integer_na_columns(df):
    """ Integer columns containing NA values are converted to Float in pandas
        This function selects these columns and converts them to back to integers
    """

    # Select data with floats
    numerical_data = df.select_dtypes(include=[np.float64])

    # Round values to 4 decimals
    # clinical_data.loc[:, numerical_data.columns] = np.round(numerical_data, 4)

    # Select columns which contain integers with NA values (numpy has converted them to floats)
    integer_na_columns = numerical_data.columns[numerical_data.apply(check_integer_na_columns, axis=0)]

    # Convert integer columns with NA to string(integer) columns
    if len(integer_na_columns) > 0:
        df.loc[:, integer_na_columns] = df.loc[:, integer_na_columns].applymap(
            lambda x: str(x).split('.')[0].replace('nan', 'NA'))
    return df


def modify_clinical_data_column_names(clinical_data_df):
    # Remove symbols from attribute names and make them uppercase
    clinical_data_df = clinical_data_df.rename(columns=lambda s: re.sub('[^0-9a-zA-Z_]+', '_', s))
    clinical_data_df = clinical_data_df.rename(columns=lambda x: x.strip('_'))
    return clinical_data_df


def modify_clinical_data_column_values(clinical_data_df):
    # Fix integers that are converted to floats due to NA in column
    if len(clinical_data_df.select_dtypes(include=[np.float64]).columns) > 0:
        clinical_data_df = fix_integer_na_columns(clinical_data_df)
    # Check if column names are unique.
    # In case of duplicates, rename them manually before or after header creation
    # TODO: Nice to have - Extract mapping dictionaries to external config, now they are hardcoded
    if not len(set(clinical_data_df.columns.tolist())) == len(clinical_data_df.columns.tolist()):
        logger.error('Attribute names not unique, not writing data_clinical. Rename them using the remap dictionary.')
        sys.exit(1)
    # Drop duplicate rows, this does not check for duplicate sample ID's
    cd_row_count = clinical_data_df.shape[0]
    clinical_data_df = clinical_data_df.loc[clinical_data_df.astype(str).drop_duplicates(keep='first').index]
    logger.debug('Found and dropped {} duplicates in the clinical data'
                 .format(cd_row_count - clinical_data_df.shape[0]))
    return clinical_data_df


def transform_patient_clinical_data(subject_registry: CentralSubjectRegistry) -> [pd.DataFrame, pd.DataFrame]:
    patient_data_df = subject_registry_to_patient_data_df(subject_registry)

    # Remove empty columns
    patient_data_df.dropna(axis=1, how='all', inplace=True)
    # Create header
    patient_data_header = create_clinical_header(patient_data_df)
    patient_data_df = modify_clinical_data_column_names(patient_data_df)
    patient_data_df = modify_clinical_data_column_values(patient_data_df)

    return patient_data_df, patient_data_header


def transform_sample_clinical_data(subject_registry: CentralSubjectRegistry) -> [pd.DataFrame, pd.DataFrame]:
    sample_data_df = subject_registry_to_sample_data_df(subject_registry)

    # Remove empty columns
    sample_data_df.dropna(axis=1, how='all', inplace=True)
    # Create header
    sample_data_header = create_clinical_header(sample_data_df)
    sample_data_df = modify_clinical_data_column_names(sample_data_df)
    sample_data_df = modify_clinical_data_column_values(sample_data_df)

    return sample_data_df, sample_data_header


def write_clinical(clinical_data, clinical_header, clinical_type, output_dir, study_id):
    # Writing clinical patient file
    clinical_filename = os.path.join(output_dir, 'data_clinical_{}.txt'.format(clinical_type))
    clinical_header.to_csv(clinical_filename, sep='\t', index=False, header=False, mode='w')
    clinical_data.to_csv(clinical_filename, sep='\t', index=False, header=True, mode='a')
    # Set clinical type for meta file
    if clinical_type == 'sample':
        meta_datatype = 'SAMPLE_ATTRIBUTES'
    elif clinical_type == 'patient':
        meta_datatype = 'PATIENT_ATTRIBUTES'
    else:
        logger.error("Unknown clinical data type")
        sys.exit(1)
    # Create meta file
    meta_filename = os.path.join(output_dir, 'meta_clinical_{}.txt'.format(clinical_type))
    create_meta_content(file_name=meta_filename,
                        cancer_study_identifier=study_id,
                        genetic_alteration_type='CLINICAL',
                        datatype=meta_datatype,
                        data_filename='data_clinical_{}.txt'.format(clinical_type))
