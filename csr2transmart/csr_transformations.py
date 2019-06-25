import os
import sys
import json
import click
import collections
import logging
import pandas as pd
from logging.config import fileConfig
from .parse_ngs_files import process_ngs_dir
from .csr_read_data import get_encoding, input_file_to_df,\
    bool_is_file, validate_source_file, check_for_codebook, set_date_fields, apply_header_map,\
    determine_file_type, check_file_list

from .csr_build_dataframe import add_biosource_identifiers, merge_entity_data_frames,\
    build_study_registry

ST_COLUMNS = {'STUDY_ID'}
PK_COLUMNS = {'INDIVIDUAL_ID', 'DIAGNOSIS_ID', 'BIOMATERIAL_ID', 'BIOSOURCE_ID'}

logger = logging.getLogger(__name__)


def read_dict_from_file(filename, path=None):
    logger.debug('Reading json file {}'.format(filename))
    file = os.path.join(path, filename)
    if os.path.exists(file):
        try:
            with open(file, 'r') as f:
                dict_ = json.loads(f.read())
            return dict_
        except ValueError as ve:
            logger.error('JSON file {} had unexpected characters. {}'.format(filename, ve))
            return None
    else:
        logger.error('Expected config file: {} - not found. Aborting'.format(file))
        sys.exit(1)


def get_study_files(file_prop_dict, columns_to_csr_map):
    exemption_set = set()
    for filename, file_items in file_prop_dict.items():
        item_list = []
        items = [i.upper() for i in file_items['headers']]
        if filename in columns_to_csr_map:
            for item in items:
                item_list.append(columns_to_csr_map[filename].get(item, item))
        else:
            item_list = items

        if determine_file_type(item_list, filename) in ['study', 'individual_study']:
            exemption_set.add(filename)
    return exemption_set


def get_overlapping_columns(file_prop_dict, columns_to_csr_map):
    """Determine which columns in the Central Subject Registry (CSR) have input from multiple files. Constructs a dict
    with conflicts grouped per CSR column. Takes two dicts which define expected headers in the input files and
    map the expected headers to the CSR datamodel.

    :param file_prop_dict: Dictionary with filename as key and headers in file as a list of values -
    FILENAME: [COLUMN_1, COLUMN_2]}
    :param columns_to_csr_map: Map input column names to the CSR data model column names -
    {FILENAME: {COLUMN_NAME: CSR_COLUMN_NAME}}
    :return: Dict with column names as keys and ordered filename lists as values. {CSR_COLUMN_NAME: [FILE_1, FILE_2]}
    """
    exemption_set = get_study_files(file_prop_dict, columns_to_csr_map)

    col_file_dict = dict()
    for filename in file_prop_dict:
        if filename in exemption_set:
            continue
        colname_dict = columns_to_csr_map[filename] if filename in columns_to_csr_map else None
        for colname in file_prop_dict[filename]['headers']:
            colname = colname.upper()
            if colname in PK_COLUMNS or colname in ST_COLUMNS:
                continue
            if colname_dict and colname in colname_dict:
                colname = colname_dict[colname]
            if colname not in col_file_dict:
                col_file_dict[colname] = [filename]
            else:
                col_file_dict[colname].append(filename)

    # Remove all columns that occur in only one file, not important to use in conflict resolution
    col_file_dict = {colname: filenames for colname, filenames in col_file_dict.items() if len(filenames) > 1}
    return col_file_dict


def check_column_prio(column_prio_dict, col_file_dict, col_prio_file, file_headers_file):
    """Compare the priority definition from column_priority.json with what was found in file_headers.json and log
    all mismatches."""
    found_error = False
    missing_in_priority = set(col_file_dict.keys()) - set(column_prio_dict.keys())
    missing_in_file_headers = set(column_prio_dict.keys()) - set(col_file_dict.keys())

    if missing_in_file_headers:
        for col in missing_in_file_headers:
            logger.warning('Priority is defined for column {0!r}, but the column was not found in the expected columns.'
                           ' Expected columns are defined in {1!r}'.format(col, file_headers_file))

    # Column name missing entirely
    if missing_in_priority:
        found_error = True
        for col in missing_in_priority:
            logger.error(
                ('{0!r} column occurs in multiple data files: {1}, but no priority is '
                 'defined. Please specify the column priority in the {2!r} JSON file.').format(
                    col, col_file_dict[col], col_prio_file
                )
            )

    # Priority present, but incomplete or unknown priority provided
    shared_columns = set(column_prio_dict.keys()).intersection(set(col_file_dict.keys()))
    for col in shared_columns:
        files_missing_in_prio = [filename for filename in col_file_dict[col] if filename not in column_prio_dict[col]]
        files_only_in_prio = [filename for filename in column_prio_dict[col] if filename not in col_file_dict[col]]
        if files_missing_in_prio:
            found_error = True
            logger.error(('Incomplete priority provided for column {0!r}. It occurs in these files: {1}, but '
                          'priority found only for the following files: {2}. Please add the missing files {3} to the '
                          'priority mapping: {4} for column: {0}').format(
                col,
                col_file_dict[col],
                column_prio_dict[col],
                list(set(col_file_dict[col]).difference(set(column_prio_dict[col]))),
                col_prio_file)
            )

        if files_only_in_prio:
            logger.warning(('Provided priority for column {0!r} contains more files than present in '
                            '{1}. The following priority files are not used: {2}').format(
                col, file_headers_file, files_only_in_prio)
            )

    if found_error:
        sys.exit(1)


def get_filelist(dir_, skip=['NGS']):
    """

    :param dir_:
    :param skip: String value of files or
    :return:
    """
    file_list = []
    for filename in os.listdir(dir_):
        if filename.startswith('.') or filename in skip or 'codebook' in filename:
            continue
        file = os.path.join(dir_, filename)
        if os.path.isdir(file):
            file_list += get_filelist(file)
        elif bool_is_file(filename, dir_):
            file_list.append(file)
        else:
            logger.warning('{} in {} not a valid clinical file, skipping'.format(filename, file))
    return file_list


def resolve_data_conflicts(df, column_priority):
    """Take in the subject registry as df and use the column priority per file to resolve conflicts.
    A conflict means data for the same column name is provided from multiple data sources.

    If conflicted columns are present in the provided dataframe but no resolution strategy is provided
    via the column_priority an error will be logged. The function will finish processing the whole dataframe
    before exiting if it finished without errors.

    Duplicated rows are dropped. Number of duplicated dropped rows is reported

    :param df: Subject registry dataframe with multi level column names
    :param column_priority: Dictionary with column name as key and an ordered list as values to indicate priority
    :return: Conflict free Subject registry with one column per mapped concept
    """
    df.set_index(list(PK_COLUMNS), inplace=True)
    missing_column = False
    # Reorder the column names from filename - column label to column label - filename
    df = df.reorder_levels(order=[1, 0], axis=1).sort_index(axis=1, level=0)
    subject_registry = pd.DataFrame()
    for column in df.columns.get_level_values(0).unique():
        if df[column].shape[1] > 1:
            # Remove columns from the dataframe that are being processed and store in a reference df
            ref_df = df.pop(column)
            if column not in column_priority:
                logger.error(
                    'Column: {} missing from column priority \
                    mapping for the following files {}'.format(column, ref_df.columns.tolist()))
                missing_column = True
                continue
            ref_files = column_priority[column]
            base = pd.DataFrame(data={column: ref_df[ref_files[0]]})
            for file in ref_files[1:]:
                base = base.combine_first(pd.DataFrame(data={column: ref_df[file]}))
            if subject_registry.empty:
                subject_registry = base.reset_index()
            else:
                subject_registry = subject_registry.merge(base.reset_index(), on=list(PK_COLUMNS), how='outer')

    df.columns = df.columns.droplevel(1)
    df.reset_index(inplace=True)

    if subject_registry.empty:
        subject_registry = df
    else:
        subject_registry = subject_registry.merge(df, on=list(PK_COLUMNS), how='outer')

    # Drop duplicated rows.
    csr_rows = subject_registry.shape[0]
    subject_registry = subject_registry.loc[~subject_registry.duplicated(keep='first'), :]
    logger.info('Dropped {} duplicated data rows'.format(csr_rows - subject_registry.shape[0]))

    if missing_column:
        logger.error('Can not resolve data conflicts due to missing columns from column priority mapping, exiting')
        sys.exit(1)

    # Conflict free df
    return subject_registry


def build_csr_dataframe(file_dict):
    """Takes the complete data dictionary with all of the read input files. Merges the data per entity type and adds
     INDIVIDUAL_ID and DIAGNOSIS_ID to the biomaterial entity. Data duplication is taken care of within entities

     Returns the complete central subject registry as a
     pandas Dataframe using pandas concat()

    :param file_dict: dictionary with all the files to be merged
    :param file_list: an ordered list of expected files
    :param csr_data_model: dictionary with the csr_data_model description
    :return: Central Subject Registry as pandas Dataframe
    """

    entity_to_columns = collections.OrderedDict()
    entity_to_columns['individual'] = ['INDIVIDUAL_ID']
    entity_to_columns['diagnosis'] = ['DIAGNOSIS_ID', 'INDIVIDUAL_ID']
    entity_to_columns['biosource'] = ['BIOSOURCE_ID', 'INDIVIDUAL_ID', 'DIAGNOSIS_ID']
    entity_to_columns['biomaterial'] = ['BIOMATERIAL_ID', 'BIOSOURCE_ID', 'INDIVIDUAL_ID', 'DIAGNOSIS_ID']

    missing_entities = False

    entity_to_data_frames = collections.OrderedDict()
    for entity, columns in entity_to_columns.items():
        if not file_dict[entity]:
            logger.error('Missing data for entity: {} does not have a corresponding file.'.format(entity))
            missing_entities = True
            continue

        if entity == 'biomaterial' and 'biosource' in entity_to_data_frames.keys():
            for filename in file_dict[entity]:
                file_dict[entity][filename] = add_biosource_identifiers(entity_to_data_frames['biosource'],
                                                                        file_dict[entity][filename])

        logger.debug('Merging data for entity: {}'.format(entity))
        df = merge_entity_data_frames(df_dict=file_dict[entity],
                                      id_columns=columns,
                                      name=entity)
        entity_to_data_frames[entity] = df

    if missing_entities:
        logger.error('Missing data for one or more entities, cannot continue.')
        sys.exit(1)

    # TODO: ADD DEDUPLICATION ACROSS ENTITIES:
    # TODO: Add advanced deduplication for double values from for example individual and diagnosis.
    # TODO: idea to capture this in a config file where per column for the CSR the main source is described.
    # TODO: This could reuse the file_header mapping to create subselections and see if there are duplicates.
    # TODO: The only thing that is not covered is some edge cases where a data point from X should lead instead of the
    # TODO: normal Y data point.

    # Concat all data starting with individual into the CSR dataframe, study, diagnosis, biosource and biomaterial
    subject_registry = pd.concat(entity_to_data_frames.values())

    return subject_registry


def read_data_files(clinical_data_dir, output_dir, columns_to_csr, file_list, file_headers, file_headers_name):
    """Loop over the clinical_data_dir and process all the clinical data. Check if all expected files and headers are in
    the input data and remap the input columns to the expected Central Subject Registry(CSR) column headers.

    :param clinical_data_dir: Path to the input directory with all clinical data
    :param output_dir: Directory in which the codebooks are stored. By default the assumption is that the codebooks are
    in the output directory
    :param columns_to_csr: dictionary with the mapped column names to the expected column names in the CSR
    :param file_list: List of expected input files
    :param file_headers: dictionary with the expected columns per file.
    :param file_headers_name: filename of the configuration file which contains the expected files and columns.
    :return: dictionary with a DataFrame dictionary per entity. Example:
    {'individual': {FILE1: DataFrame, FILE2: DataFrame},'diagnosis':{DIA DATAFILE: DataFrame}}
    """
    # TODO: reconsider if check can be done separately from processing
    files_per_entity = {'individual': {},
                        'diagnosis': {},
                        'biosource': {},
                        'biomaterial': {},
                        'study': {},
                        'individual_study': {}
                        }
    exit_after_process = []

    files_found = {filename: False for filename in file_list}

    clinical_files = get_filelist(clinical_data_dir)

    date_errors = []
    incorrect_files = []
    file_type_error = False
    codebook_mapping_error = []
    for file in clinical_files:
        filename = os.path.basename(file)

        if filename in files_found:
            files_found[filename] = True

        validate_error = validate_source_file(file_headers, file, file_headers_name)
        if validate_error:
            exit_after_process.append(file)
            continue

        # Check if codebook is available for filename, if not codebook will be None
        codebook = check_for_codebook(filename, output_dir)

        # Read data from file and create a pandas DataFrame. If a header mapping is provided the columns
        # are mapped before the DataFrame is returned
        df, mapping_status = input_file_to_df(filename=file, encoding=get_encoding(file), codebook=codebook)
        if not mapping_status:
            codebook_mapping_error.append(file)

        # Update date format
        date_errors.append(set_date_fields(df, file_headers, filename))

        # Check if mapping for columns to CSR fields is present
        header_map = columns_to_csr[filename] if filename in columns_to_csr else None
        if header_map:
            df.columns = apply_header_map(df.columns, header_map)
        columns = df.columns

        # Check if headers are present
        file_type = determine_file_type(columns, filename)
        if not file_type:
            file_type_error = True
            incorrect_files.append(filename)
            continue
        files_per_entity[file_type].update({filename: df})

    # Check if any errors were found in the input data and provide error messages before exiting.
    if codebook_mapping_error:
        logger.error('Found codebook mapping errors for {}. See ERRORs above for more information'.format(
            codebook_mapping_error))

    if any(date_errors):
        logger.error('Found incorrect date formats for {} input files'.format(sum(date_errors)))

    if len(exit_after_process) > 0:
        logger.error('Validation failed for the following files {}. Look at the error messages above for more detailed '
                     'information.'.format(exit_after_process))

    if file_type_error:
        logger.error('Could not determine file types for {}, missing identifying keys. Please add one of the '
                     'identifying keys {}'.format(incorrect_files, ST_COLUMNS.update(PK_COLUMNS)))

    # if any of the errors are found the program should exit
    if len(exit_after_process) > 0 or any(date_errors) or file_type_error or codebook_mapping_error:
        sys.exit(1)

    missing_expected_files = check_file_list(files_found)
    if missing_expected_files:
        logger.error('Missing expected files. For more information see errors above')
        sys.exit(1)

    return files_per_entity


def get_configuration(data_model, file_headers, columns_to_csr, column_priority, config_dir):
    """ Parse configuration files and return set of dictionaries

    :param data_model: json file describing the data model. Format: {"central_subject_registry: {ENTITY: [COL1, COL2],
    ENTITY2: [...]}, "study_registry": {...}}
    :param file_headers: json file with headers per file, indicate dateformat in file, indicate date columns.
    Format: {Filename: {"headers":[col1, col2], "date_format": datetime strptime format, "date_columns": [col2]}}
    :param columns_to_csr: json file with mapping from input file header to CSR expected header. Format:
    {Filename: Current_header: Expected CSR header}. Expected CSR header should be defined in data_model.
    :param column_priority: json file to indicate file priority per column for data conflict resolution. Format:
    {column_header: [file1, file2], column_header2: [...]}. Order of files in list matters. Column_headers as defined in
    data_model
    :param config_dir: Path to directory where the configs are stored
    :return: Dictionaries and lists of expected files
    """
    data_model_ = read_dict_from_file(filename=data_model, path=config_dir)
    file_prop_dict = read_dict_from_file(filename=file_headers, path=config_dir)
    columns_to_csr_map = read_dict_from_file(filename=columns_to_csr, path=config_dir)
    column_prio_dict = read_dict_from_file(filename=column_priority, path=config_dir)

    read_dicts = [data_model_, file_prop_dict, columns_to_csr_map, column_prio_dict]

    if len([l for l in read_dicts if l is None]) > 0:
        sys.exit(1)

    if 'central_subject_registry' in data_model_:
        csr_data_model = data_model_['central_subject_registry']
    else:
        logger.error('"central_subject_registry" object missing from the {} JSON file, exiting'.format(data_model))
        sys.exit(1)
    if 'study_registry' in data_model_:
        study_data_model = data_model_['study_registry']
    else:
        logger.error('"study_registry" object missing from the {} JSON file, exiting'.format(data_model))
        sys.exit(1)

    # Uppercase items in dictionaries
    columns_to_csr_map = {k: {k.upper(): v.upper() for k, v in vals.items()} for k, vals in columns_to_csr_map.items()}
    column_prio_dict = {k.upper(): files for k, files in column_prio_dict.items()}

    # Check if there are overlapping columns and see if all columns are provided with conflict resolution rules.
    col_file_dict = get_overlapping_columns(file_prop_dict, columns_to_csr_map)
    check_column_prio(column_prio_dict=column_prio_dict,
                      col_file_dict=col_file_dict,
                      col_prio_file=column_priority,
                      file_headers_file=file_headers)

    expected_files = file_prop_dict.keys()

    return columns_to_csr_map, expected_files, file_prop_dict, csr_data_model, study_data_model, column_prio_dict


def extend_subject_registry(csr, input_dir):
    # NGS DATA
    ngs_data_dir = None
    for parent_dir, dirs, files in os.walk(input_dir):
        if 'NGS' in dirs:
            ngs_data_dir = os.path.join(parent_dir, dirs[dirs.index('NGS')])
            logger.info('Found NGS data directory: {}'.format(ngs_data_dir))
            break
    if ngs_data_dir is None:
        logger.info('No NGS data found.')
        return csr
    ngs_data = process_ngs_dir(ngs_data_dir)
    csr_update = csr.merge(ngs_data, on=['BIOSOURCE_ID', 'BIOMATERIAL_ID'], how='outer', indicator=True)

    # report biomaterials that do not have clinical data
    missing_biomaterials = set()
    for i, row in csr_update[['BIOMATERIAL_ID', '_merge']].iterrows():
        if row['_merge'] == 'right_only':
            missing_biomaterials.add(row['BIOMATERIAL_ID'])
    if missing_biomaterials != set():
        logger.warning('Following biomaterials found in NGS data but excluded from CSR due to missing clinical data:'
                       ' {}'.format(missing_biomaterials))
    drop_index = csr_update.loc[csr_update['_merge'] == 'right_only', :].index
    csr_update = csr_update.drop(columns='_merge', index=drop_index)

    # Additional helper variables
    # Count of unique diagnosis Ids per patient
    logger.info('Counting number of diagnoses per patient')
    # Adjusts the CSR inplace
    add_diagnosis_counts(csr_update, colname='DIAGNOSIS_COUNT')

    # Diff between date of birth and date of diagnosis (first diagnosis)
    logger.info('Calculating age at first diagnosis')
    # Adjusts the CSR inplace
    date_error = calculate_age_at_diagnosis(csr_update, 'AGE_FIRST_DIAGNOSIS')
    if date_error:
        logger.error('Errors found during data processing, exiting')
        sys.exit(1)

    return csr_update


def add_diagnosis_counts(csr, colname):
    ind = 'INDIVIDUAL_ID'
    dia = 'DIAGNOSIS_ID'
    csr[colname] = pd.np.nan

    for individual in csr[ind].unique():
        subset = csr[csr[ind] == individual]
        count = subset[dia].dropna().unique().size
        csr.loc[(csr[ind] == individual) & (csr[dia].isnull()), colname] = count


def calculate_age_at_diagnosis(csr, colname, date_format='%Y-%m-%d'):
    error_found = False
    ind = 'INDIVIDUAL_ID'
    dia = 'DIAGNOSIS_ID'
    csr[colname] = pd.np.nan
    dt_csr = csr[['INDIVIDUAL_ID', 'DIAGNOSIS_ID', 'BIRTH_DATE', 'DIAGNOSIS_DATE']].copy()
    try:
        dt_csr['BIRTH_DATE'] = pd.to_datetime(dt_csr['BIRTH_DATE'], format=date_format)
    except ValueError as ve:
        logger.error('Failed to convert birth date column to dates with specified format {}. Error: {}'
                     .format(date_format, ve))
        error_found = True

    try:
        dt_csr['DIAGNOSIS_DATE'] = pd.to_datetime(dt_csr['DIAGNOSIS_DATE'], format=date_format)
    except ValueError as ve:
        logger.error('Failed to convert diagnosis date column to dates with specified format {}. Error: {}'
                     .format(date_format, ve))
        error_found = True

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
            error_found = True

    return error_found


def csr_transformation(input_dir, output_dir, config_dir, data_model,
                       column_priority, file_headers, columns_to_csr, output_filename, output_study_filename):

    # Get reference dictionaries and lists
    columns_to_csr_map,\
        expected_files,\
        file_prop_dict,\
        csr_data_model,\
        study_data_model,\
        column_prio_dict = get_configuration(data_model=data_model,
                                             config_dir=config_dir,
                                             file_headers=file_headers,
                                             columns_to_csr=columns_to_csr,
                                             column_priority=column_priority)

    # set output directory
    output_file = os.path.join(output_dir, output_filename)
    study_output_file = os.path.join(output_dir, output_study_filename)

    # Read in the data files per entity
    files_per_entity = read_data_files(clinical_data_dir=input_dir,
                                       output_dir=output_dir,
                                       columns_to_csr=columns_to_csr_map,
                                       file_list=expected_files,
                                       file_headers=file_prop_dict,
                                       file_headers_name=file_headers)

    study_registry = build_study_registry(study=files_per_entity.pop('study'),
                                          ind_study=files_per_entity.pop('individual_study'),
                                          csr_data_model=csr_data_model)

    logger.info('Study registry built')

    # Use read in data to build the Central Subject Registry
    subject_registry = build_csr_dataframe(file_dict=files_per_entity)

    logger.info('Subject registry built')

    subject_registry = resolve_data_conflicts(df=subject_registry,
                                              column_priority=column_prio_dict)

    subject_registry = extend_subject_registry(subject_registry, input_dir)

    # Drop columns from the subject registry that are captured in the study registry
    columns_to_drop = {col for col_list in study_data_model.values() for col in col_list if col not in PK_COLUMNS}
    subject_registry = subject_registry.drop(columns=columns_to_drop, errors='ignore')

    # Check if all fields expected in the CSR dataframe are present. The expected columns are derived from the CSR data
    # model
    csr_expected_header = []
    for key in csr_data_model:
        csr_expected_header += list(csr_data_model[key])
    missing_header = [l for l in csr_expected_header if l not in subject_registry.columns]
    if len(missing_header) > 0:
        logger.warning('Missing columns from Central Subject Registry data model: {}'.format(missing_header))
        # sys.exit(1) #Should this exit?

    if pd.isnull(subject_registry['INDIVIDUAL_ID']).any():
        # TODO extend error message here to include pointers to files?
        logger.error('Found data rows with no individual or patient identifier')
        sys.exit(1)
        # logger.warning('HEADSUP! for testing removing incorrect data')
        # subject_registry= subject_registry[~subject_registry.INDIVIDUAL_ID.isnull()]

    logger.info('Writing CSR data to {}'.format(output_file))
    subject_registry.to_csv(output_file, sep='\t', index=False)

    logger.info('Writing Study registry data to {}'.format(study_output_file))
    study_registry.to_csv(study_output_file, sep='\t', index=False)

    return


@click.command()
@click.option('--input_dir', type=click.Path(exists=True))
@click.option('--output_dir', type=click.Path(exists=True))
@click.option('--config_dir', type=click.Path(exists=True))
@click.option('--data_model', default=None)
@click.option('--column_priority', default=None)
@click.option('--file_headers', default=None)
@click.option('--columns_to_csr', default=None)
@click.option('--output_filename', default='csr_data_transformation.tsv')
@click.option('--output_study_filename', default='study_registry.tsv')
@click.option('--logging_config', default=None)
def csr_transformations(input_dir, output_dir, config_dir, data_model,
                        column_priority, file_headers, columns_to_csr, output_filename, output_study_filename,
                        logging_config):

    # Check if mandatory parameters are set
    mandatory = {'--config_dir': config_dir, '--data_model': data_model, '--column_priority': column_priority,
                 '--columns_to_csr': columns_to_csr, '--file_headers': file_headers, '--input_dir': input_dir,
                 '--output_dir': output_dir, '--logging_config': logging_config,
                 '--output_study_file': output_study_filename}
    if not all(mandatory.values()):
        for option_name, option_value in mandatory.items():
            if not option_value:
                print('Input argument missing: {}'.format(option_name))
        sys.exit(1)

    # set logging when calling function directly, temporary ugly hack
    global logger
    fileConfig(logging_config)
    logger = logging.getLogger('csr_transformations')

    csr_transformation(input_dir, output_dir, config_dir, data_model,
                       column_priority, file_headers, columns_to_csr, output_filename, output_study_filename)

    sys.exit(0)


def main():
    csr_transformations()


if __name__ == '__main__':
    main()
