import os
import pandas as pd
import json
import chardet
import logging

ALLOWED_ENCODINGS = {'utf-8', 'ascii'}

logger = logging.getLogger(__name__)


def get_encoding(filename):
    """Open the file and determine the encoding, returns the encoding cast to lower"""
    with open(filename, 'rb') as file:
        # read file and determine encoding
        read_file = file.read()
        file_encoding = chardet.detect(read_file)['encoding'].lower()
        logger.debug('Found {} encoding for {}'.format(file_encoding, os.path.basename(filename)))

        if file_encoding == 'iso-8859-1':
            try:
                read_file.decode('utf-8')
                logger.warning('Found iso-8859-1 encoding for {} but attempted decode with utf-8 successful, '
                               'assuming utf-8'.format(filename))
                return 'utf-8'
            except UnicodeDecodeError as ude:
                logger.error('Could not decode file with utf-8, keeping iso-8859-1 for {}. {}'.format(filename, ude))
                return file_encoding
        else:
            return file_encoding


def input_file_to_df(filename, encoding, seperator=None, codebook=None):
    """Read in a DataFrame from a plain text file. Columns are cast to uppercase.
     If a column_mapping is specified the columns will also be tried to map.
     If a codebook was specified it will be applied before the column mapping"""
    logger.debug('Reading {} to a dataframe'.format(filename))
    df = pd.read_csv(filename, sep=seperator, encoding=encoding, dtype=object, engine="python")
    df.columns = map(lambda x: str(x).upper(), df.columns)

    # If codebook is not None, apply codebook
    apply_map = True  # Flag to see if codebook is complete to apply
    if codebook:
        # Check if all values in data file are in the code books
        for column_name, mapping in codebook.items():
            column_data = df.get(column_name, pd.Series())
            if column_data.any():
                non_empty_columns = column_data[~column_data.isin([pd.np.nan, ''])]
                diff = set(non_empty_columns).difference(set(mapping.keys()))
                if diff:  # if the set is not empty
                    apply_map = False
                    logger.error('Value(s) {} in datafile {} not found in the provided codebook'.format(diff, filename))

        if apply_map:  # Skip if incomplete mapping
            logger.debug('Applying codebook to {}'.format(filename))
            df.replace(codebook, inplace=True)
    return df, apply_map


def bool_is_file(filename, path):
    """If filename is not a file, has codebook in its name or starts with a . returns False, else True
    """
    path_ = os.path.join(path, filename)
    if 'codebook' in filename.lower():
        return False
    if filename.startswith('.'):
        return False

    return os.path.isfile(path_)


def validate_source_file(file_prop_dict, path, file_headers_name):
    """
    Checks file encoding, headers. Checks if all expected files are present and logs if files that are not defined in
    the config files are encountered

    Expected file_prop_dict format: {FILENAME: {DATE_FORMAT: datetime strptime format, DATE_COLUMNS: ['col1', 'col2']}}


    :param file_prop_dict: dict with expected headers as a list, date_format and date_columns as list to update.
    :param path: Path to the file
    :param file_headers_name: dict with list of expected file headers per dataframe
    :return: returns True if errors are found, else False
    """
    filename = os.path.basename(path)

    # Check file is not empty
    if os.stat(path).st_size == 0:
        logger.error('File is empty: {}'.format(filename))
        return True

    # Check encoding
    encoding = get_encoding(path)
    if encoding not in ALLOWED_ENCODINGS:
        logger.error('Invalid file encoding {0!r} detected for: {1}. Must be {2}.'.format(
            encoding,
            filename,
            '/'.join(ALLOWED_ENCODINGS))
        )
        return True

    # Try to read the file as df
    try:
        df = pd.read_csv(path, sep=None, engine='python', dtype='object')
    except ValueError:  # Catches far from everything
        logger.error('Could not read file: {}. Is it a valid data frame?'.format(filename))
        return True
    else:
        df.columns = [field.upper() for field in df.columns]
        file_header_fields = set(df.columns)

    # Check mandatory header fields are present
    if filename in file_prop_dict:
        required_header_fields = {field.upper() for field in file_prop_dict[filename]['headers']}
        if not required_header_fields.issubset(file_header_fields):
            missing = required_header_fields - file_header_fields
            logger.warning('{0} is missing mandatory header fields: {1}'.format(filename, missing))
        return False
    else:
        logger.error('Found file {}, but not defined in {}'.format(filename, file_headers_name))
        return True


def check_for_codebook(filename, path):
    """ Check if the filename has a corresponding codebook that is stored in the path dir.
    The filename is used to search for <filename>_codebook.<filename extension>.json
    """
    f_name, f_extension = filename.rsplit('.', 1)
    code_file = '{}_codebook.{}.json'.format(f_name, f_extension)
    if code_file in os.listdir(path):
        with open(os.path.join(path, code_file), 'r') as cf:
            codebook = json.loads(cf.read())
        return codebook
    else:
        return None


def set_date_fields(df, file_prop_dict, filename):
    """Changes the input date format to a predefined date string expected by the pipeline. Input date formats have to
    be specified in the file_prop_dict under the date_format field and columns to which the date format is applied
    should be provided as a list of column names in the date_columns field.

    Expected file_prop_dict format: {FILENAME: {DATE_FORMAT: datetime strptime format, DATE_COLUMNS: ['col1', 'col2']}}

    :param df: pandas DataFrame object where the date fields need to be set
    :param file_prop_dict: dictionary with date_format and date_columns to update per file
    :param filename: filename of file being processed. Used to select correct header list
    :return: returns None, Dataframe is adjusted in place
    """
    date_error = False
    date_fields = file_prop_dict[filename].get('date_columns')
    date_fields = [field.upper() for field in date_fields] if date_fields else None

    if date_fields:
        expected_date_format = file_prop_dict[filename].get('date_format')
        logger.info('Setting date fields for {}'.format(filename))
        for col in date_fields:
            try:
                df[col] = df[col].apply(get_date_as_string, args=(expected_date_format,))
            except ValueError as ve:
                logger.error('Incorrect date format for {0} in column {1}, expected {2}.'
                             'error message: {3}'.format(filename,
                                                         col,
                                                         expected_date_format,
                                                         ve))
                date_error = True
                continue
    else:
        logger.debug('There are no expected date fields to check for {}'.format(filename))

    return date_error


def get_date_as_string(item, dateformat, str_format='%Y-%m-%d'):
    if pd.isnull(item):
        return pd.np.nan
    else:
        return pd.datetime.strptime(item, dateformat).strftime(str_format)


def apply_header_map(df_columns, header):
    """Generate a new header for a pandas Dataframe using either the column name or the mapped column name if provided
    in the header object. Returns uppercased column names from the header"""
    header_upper = {k.upper(): v.upper() for k, v in header.items()}
    new_header = [header_upper[col] if col in header_upper else col for col in df_columns]
    return new_header


def determine_file_type(columns, filename):
    """Based on pandas DataFrame columns determine the type of entity to assign to the dataframe."""
    file_type = None
    if 'BIOMATERIAL_ID' in columns:
        file_type = 'biomaterial'
    elif 'BIOSOURCE_ID' in columns:
        file_type = 'biosource'
    elif 'DIAGNOSIS_ID' in columns:
        file_type = 'diagnosis'
    elif 'STUDY_ID' in columns and 'INDIVIDUAL_ID' not in columns:
        file_type = 'study'
    elif 'STUDY_ID' in columns:
        file_type = 'individual_study'
    elif 'INDIVIDUAL_ID' in columns:
        file_type = 'individual'

    if file_type:
        logger.info('Filetype {!r} for file {}'.format(file_type, filename))
    else:
        logger.error(('No key identifier found (individual, diagnosis, study, biosource, '
                      'biomaterial) in {}'.format(filename)))

    return file_type


def check_file_list(files_found):
    error = False
    for filename, found in files_found.items():
        if not found:
            error = True
            logger.error('Data file: {!r} expected but not found in source folder.'.format(filename))

    return error
