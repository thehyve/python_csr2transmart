import logging
import os
import sys

import pandas as pd

from csr2transmart.parse_ngs_files import process_ngs_dir

logger = logging.getLogger(__name__)


class HelperVariablesException(Exception):
    pass


def get_ngs_data(input_dir) -> pd.DataFrame:
    ngs_data_dir = None
    for parent_dir, dirs, files in os.walk(input_dir):
        if 'NGS' in dirs:
            ngs_data_dir = os.path.join(parent_dir, dirs[dirs.index('NGS')])
            logger.info('Found NGS data directory: {}'.format(ngs_data_dir))
            break
    if ngs_data_dir is None:
        logger.info('No NGS data found.')
        return pd.DataFrame()
    return process_ngs_dir(ngs_data_dir)


def count_number_of_diagnosis_per_patient(csr, colname):
    ind = 'INDIVIDUAL_ID'
    dia = 'DIAGNOSIS_ID'
    csr[colname] = pd.np.nan

    for individual in csr[ind].unique():
        subset = csr[csr[ind] == individual]
        count = subset[dia].dropna().unique().size
        csr.loc[(csr[ind] == individual) & (csr[dia].isnull()), colname] = count
    return csr


def calculate_age_at_diagnosis(csr, colname, date_format='%Y-%m-%d'):
    ind = 'INDIVIDUAL_ID'
    dia = 'DIAGNOSIS_ID'
    csr[colname] = pd.np.nan
    dt_csr = csr[['INDIVIDUAL_ID', 'DIAGNOSIS_ID', 'BIRTH_DATE', 'DIAGNOSIS_DATE']].copy()
    try:
        dt_csr['BIRTH_DATE'] = pd.to_datetime(dt_csr['BIRTH_DATE'], format=date_format)
    except ValueError as ve:
        logger.error('Failed to convert birth date column to dates with specified format {}. Error: {}'
                     .format(date_format, ve))
        raise HelperVariablesException()

    try:
        dt_csr['DIAGNOSIS_DATE'] = pd.to_datetime(dt_csr['DIAGNOSIS_DATE'], format=date_format)
    except ValueError as ve:
        logger.error('Failed to convert diagnosis date column to dates with specified format {}. Error: {}'
                     .format(date_format, ve))
        raise HelperVariablesException()

    for individual in dt_csr[ind].unique():
        subset = dt_csr[dt_csr[ind] == individual]

        # Skip if individual does not have diagnosis data
        if subset.empty:
            continue

        subset = subset.sort_values('DIAGNOSIS_DATE')
        birth_date = subset.loc[(subset['BIRTH_DATE'].notnull()) & (subset[dia].isnull()), 'BIRTH_DATE']
        first_diagnosis_date = subset.loc[subset.first_valid_index(), 'DIAGNOSIS_DATE']
        if birth_date.empty or pd.isnull(first_diagnosis_date):
            logger.warning('Assigning NaN age at diagnosis for {}. Diagnosis date: {} - Birth date: {}'
                           .format(individual, first_diagnosis_date, birth_date.values[0]))
            csr.loc[(csr[ind] == individual) & (csr[dia].isnull()), colname] = pd.np.nan
            continue
        try:
            # days = (first_diagnosis_date - birth_date).dt.days.values[0]
            years = pd.Series(first_diagnosis_date - birth_date).astype('<m8[Y]').values[0]
            csr.loc[(csr[ind] == individual) & (csr[dia].isnull()), colname] = years
        except TypeError:
            logger.error('Failed to calculate age at diagnosis for {}. Diagnosis date: {} - Birth date: {}'
                         .format(individual, first_diagnosis_date, birth_date.values[0]))
            raise HelperVariablesException()


def calculate_helper_variables(csr, input_dir):
    # NGS DATA
    ngs_data = get_ngs_data(input_dir)
    if ngs_data.empty:
        return csr

    csr_update = csr.merge(ngs_data, on=['BIOSOURCE_ID', 'BIOMATERIAL_ID'], how='outer', indicator=True)

    # report biomaterials that do not have clinical data
    missing_biomaterials = set()
    for i, row in csr_update[['BIOMATERIAL_ID', '_merge']].iterrows():
        if row['_merge'] == 'right_only':
            missing_biomaterials.add(row['BIOMATERIAL_ID'])
    if missing_biomaterials != set():
        logger.warning(
            'Following biomaterials found in NGS data but excluded from CSR due to missing clinical data:'
            ' {}'.format(missing_biomaterials))
    drop_index = csr_update.loc[csr_update['_merge'] == 'right_only', :].index
    csr_update = csr_update.drop(columns='_merge', index=drop_index)

    # Additional helper variables
    # Count of unique diagnosis Ids per patient
    logger.info('Counting number of diagnoses per patient')
    # Adjusts the CSR inplace
    count_number_of_diagnosis_per_patient(csr_update, colname='DIAGNOSIS_COUNT')

    try:
        # Diff between date of birth and date of diagnosis (first diagnosis)
        logger.info('Calculating age at first diagnosis')
        # Adjusts the CSR inplace
        calculate_age_at_diagnosis(csr_update, 'AGE_FIRST_DIAGNOSIS')
    except HelperVariablesException:
        logger.error('Errors found during data processing, exiting')
        sys.exit(1)

    return csr_update
