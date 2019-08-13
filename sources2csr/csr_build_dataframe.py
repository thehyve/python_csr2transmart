import sys
import logging
import pandas as pd


logger = logging.getLogger(__name__)


def add_biosource_identifiers(biosource, biomaterial, biosource_merge_on='BIOSOURCE_ID',
                              biomaterial_merge_on='SRC_BIOSOURCE_ID'):
    """Merges two pandas DataFrames adding predefined columns from the biosource to the biomaterial

    Input dataframes are expected to have MultiIndexs with INDIVIDUAL_ID, DIAGNOSIS_ID, BIOSOURCE_ID and BIOMATERIAL_ID
    on the top level of the index. Level 0 (first level) of the column names contain identifying columns and file names.
    Level 1 (second level) of the column names should be the other column names that are in each file.
    predefined columns to be added: INDIVIDUAL_ID, DIAGNOSIS_ID

    :param biosource: a pandas DataFrame with identifiers that have to be merged into biomaterial
    :param biomaterial: a pandas DataFrame to which the identifiers will be added
    :param biosource_merge_on: A column name
    :param biomaterial_merge_on: The column containing the identifiers to use
    :return: biomaterial DataFrame with added predefined identifier columns
    """
    logger.debug('Adding biosource identifiers: Biosource ID column: {}, Biomaterial biosource ID column: {}'.format(
        biosource_merge_on, biomaterial_merge_on
    ))
    bios = biosource[['INDIVIDUAL_ID', 'BIOSOURCE_ID', 'DIAGNOSIS_ID']].copy()
    biom = biomaterial.copy()

    # Update column headers to be in line with Multiindex construct (level 0 IDs and file names, level 1 other names)
    bios.columns = bios.columns.map('|'.join)
    biom.columns = ['|'.join([col, '']) for col in biom.columns]

    # Update 'merge on' columns to be in line with column names of the data frames
    biomaterial_merge_on = '|'.join([biomaterial_merge_on, ''])
    biosource_merge_on = '|'.join([biosource_merge_on, ''])

    # Add identifiers to biomaterial data frame for all biomaterials.
    df = biom.merge(bios,
                    left_on=biomaterial_merge_on,
                    right_on=biosource_merge_on,
                    how='left')

    # Restore column names for identifying columns back to input format
    df.columns = [i.split('|')[0] for i in df.columns]
    return df


def merge_entity_data_frames(df_dict, id_columns, name):
    # TODO docstring
    logger.debug('Merging data frames for {} entity'.format(name))
    df_list = []
    key_list = []
    duplicate_index = False

    for key in df_dict.keys():
        try:
            df_ = df_dict[key].set_index(id_columns)
            if df_.index.duplicated().any():
                duplicate_index = True
                logger.error('Found unexpected duplicates in index columns {} for file: {}'.format(id_columns, key))
                continue
            df_list.append(df_dict[key].set_index(id_columns))
            key_list.append(key)
        except KeyError as ke:
            logger.error('Failed to merge dataframes for entity {}. Missing one or more identifying columns {}.\
                KeyError: {}'.format(name, id_columns, ke))
            sys.exit(1)

    if duplicate_index:
        sys.exit(1)

    logger.debug('Concatenating the following dataframes into entity dataframe: {}'.format(key_list))

    df = pd.concat(df_list, keys=key_list, join='outer', axis=1)
    if len(id_columns) < 2:
        df.index.name = (id_columns[0], '')
    df.reset_index(inplace=True)
    return df


def build_study_registry(study, ind_study, csr_data_model):
    if len(study.keys()) < 1:
        logger.error('Missing "study entity" data! Exiting')
        sys.exit(1)
    elif len(study.keys()) > 1:
        logger.warning('Found more than one input file for study entity, trying to merge and '
                       'resolve conflicts')
        # Merge study_files
        study_ = merge_study_files(study,
                                   ['STUDY_ID'],
                                   csr_data_model['study'],
                                   'study')
    else:
        study_ = study.popitem()[1].copy()

    # check if STUDY_ID is unique
    if study_['STUDY_ID'].duplicated().any():
        logger.error('Duplicated identifiers for STUDY_ID found, this will cause problems when merged with the '
                     'INDIVIDUAL_STUDY entity. Please resolve the duplicates: '
                     .format(study_.loc[study_['STUDY_ID'].duplicated(), 'STUDY_ID'].tolist()))
        sys.exit(1)

    logger.info('No errors found in STUDY entity data')

    if len(ind_study.keys()) < 1:
        logger.error('Missing "individual study" entity data! Exiting')
        sys.exit(1)
    elif len(ind_study.keys()) > 1:
        logger.warning('Found more than one input file for individual study entity, trying to merge and'
                       'resolve conflicts')
        # Merge individual_study_files
        ind_study_ = merge_study_files(ind_study,
                                       ['INDIVIDUAL_ID', 'STUDY_ID'],
                                       csr_data_model['individual_study'],
                                       'individual_study')
    else:
        ind_study_ = ind_study.popitem()[1].copy()
    logger.debug('No errors found in INDIVIDUAL_STUDY entity data')

    df = enrich_study_entity(study_, ind_study_)

    return df


def merge_study_files(df_dict, id_columns, ref_columns, entity):
    logger.info('Concatenating data for {} entity'.format(entity))
    concat = {}

    found_duplicate_in_study = []
    for file, df in df_dict().items():
        if entity == 'study' and df[id_columns].duplicated().any():
            logger.error('Found duplicates in file {!r} for identifying columns {}.'.format(file, id_columns))
            found_duplicate_in_study.append(file)
        concat[file] = all([True if col in ref_columns else False for col in df.columns])
    if len(found_duplicate_in_study) > 0:
        logger.error('Found duplicated identifiers in the following files {}'.format(found_duplicate_in_study))
        sys.exit(1)

    if all(concat.values()):
        mdf = pd.concat(df_dict.values())
        mdf.drop_duplicates(subset=id_columns, inplace=True, keep='first')
    else:
        logger.error('Could not merge input files for {} entity'.format(entity))
        for key, value in concat.items():
            if not value:
                logger.error('Missing columns defined in data_model.json for file: {}'.format(key))
        sys.exit(1)

    return mdf


def enrich_study_entity(study, ind_study):
    pk_study = 'STUDY_ID'
    pk_ind = 'INDIVIDUAL_ID'

    logger.info('Combining INDIVIDUAL_STUDY and STUDY entity data')
    merged_ind_study = ind_study.merge(study, on=pk_study, how='left')
    logger.debug('Combining done')

    enriched_ind_study = None
    for study_id in merged_ind_study[pk_study].unique():
        subset = merged_ind_study[merged_ind_study.loc[:, pk_study] == study_id]
        if (subset[pk_ind].value_counts() > 2).any():
            logger.error('Individual_study entity has duplicate INDIVIDUALS IDs for study {}. INDIVIDUALS: {}'.format(
                study_id,
                subset.loc[subset[pk_ind].duplicated(keep='first'), pk_ind].unique())
            )
            sys.exit(1)
        if subset[pk_ind].isna().any():
            logger.warning('Found empty PMC Patient IDs (INDIVIDUAL_IDs) for study {}. Skipping study'.format(study_id))
        # Update column names with study_id
        subset.columns = ['|'.join([col, study_id]) if col != pk_ind else col for col in subset.columns]
        if enriched_ind_study is not None:
            enriched_ind_study = enriched_ind_study.merge(subset, on=pk_ind, how='outer')
        else:
            enriched_ind_study = subset.copy()
    logger.debug('Return study object')
    return enriched_ind_study
