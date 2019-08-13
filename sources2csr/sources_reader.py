import collections
import logging
import os
from math import isnan
from typing import Any, Tuple, Dict, Union

import pandas as pd

from csr.csr import CentralSubjectRegistry, StudyRegistry, Study, IndividualStudy, Individual, Diagnosis, Biomaterial, \
    Biosource
from sources2csr.data_exception import DataException
from sources2csr.priority_checker import PriorityChecker
from sources2csr.utils import read_dict_from_file, get_filelist
from .helper_variables import calculate_helper_variables
from .csr_build_dataframe import add_biosource_identifiers, merge_entity_data_frames, \
    build_study_registry
from .csr_read_data import get_encoding, input_file_to_df, \
    validate_source_file, check_for_codebook, set_date_fields, apply_header_map, \
    determine_file_type, check_file_list

ST_COLUMNS = {'STUDY_ID'}
PK_COLUMNS = {'INDIVIDUAL_ID', 'DIAGNOSIS_ID', 'BIOMATERIAL_ID', 'BIOSOURCE_ID'}

logger = logging.getLogger(__name__)


def format_column(column: Union[str, Tuple[str, str]]):
    if isinstance(column, str):
        return column.lower()
    return column[0].lower() if column[1] is '' else column[1].lower()


def format_value(schema: Dict, column: str, value: Any):
    if column not in schema['properties']:
        return None
    if isinstance(value, float) and isnan(value):
        return None
    return value


def transform_entity(values: Dict[Any, Any], schema: Dict) -> Dict:
    return {format_column(k): format_value(schema, format_column(k), v)
            for k, v in values.items()}


def transform_entities(entities_df: Any, schema: Dict, constructor: Any):
    entities = [transform_entity(entity, schema) for entity in entities_df.to_dict(orient='records')]
    return [constructor(entity) for entity in entities]


class SourcesReader:

    def __init__(self, input_dir, output_dir, config_dir):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.file_prop_dict = None
        self.columns_to_csr_map = None
        self.column_prio_dict = None
        self.csr_data_model = None
        self.study_data_model = None
        self.expected_files = None
        self.read_configuration(config_dir)

    def read_configuration(self, config_dir):
        """ Parse configuration files and return set of dictionaries

        :param config_dir: Path to directory where the configs are stored
        """

        data_model_ = read_dict_from_file(filename='data_model.json', path=config_dir)
        self.file_prop_dict = read_dict_from_file(filename='file_headers.json', path=config_dir)
        self.columns_to_csr_map = read_dict_from_file(filename='columns_to_csr.json', path=config_dir)
        self.column_prio_dict = read_dict_from_file(filename='column_priority.json', path=config_dir)

        if 'central_subject_registry' in data_model_:
            self.csr_data_model = data_model_['central_subject_registry']
        else:
            logger.error('"central_subject_registry" object missing from the data_model.json file, exiting')
            raise DataException()
        if 'study_registry' in data_model_:
            self.study_data_model = data_model_['study_registry']
        else:
            logger.error('"study_registry" object missing from the data_model.json file, exiting')
            raise DataException()

        # Uppercase items in dictionaries
        self.columns_to_csr_map = {k: {k.upper(): v.upper() for k, v in vals.items()}
                                   for k, vals in self.columns_to_csr_map.items()}
        column_prio_dict = {k.upper(): files for k, files in self.column_prio_dict.items()}

        # Check if there are overlapping columns and see if all columns are provided with conflict resolution rules.
        priority_checker = PriorityChecker(self.file_prop_dict, self.columns_to_csr_map, column_prio_dict)
        priority_checker.check_column_prio()

        self.expected_files = self.file_prop_dict.keys()

    def resolve_data_conflicts(self, df):
        """Take in the subject registry as df and use the column priority per file to resolve conflicts.
        A conflict means data for the same column name is provided from multiple data sources.

        If conflicted columns are present in the provided dataframe but no resolution strategy is provided
        via the column_priority an error will be logged. The function will finish processing the whole dataframe
        before exiting if it finished without errors.

        Duplicated rows are dropped. Number of duplicated dropped rows is reported

        :param df: Subject registry dataframe with multi level column names
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
                if column not in self.column_prio_dict:
                    logger.error(
                        'Column: {} missing from column priority \
                        mapping for the following files {}'.format(column, ref_df.columns.tolist()))
                    missing_column = True
                    continue
                ref_files = self.column_prio_dict[column]
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
            raise DataException()

        # Conflict free df
        return subject_registry

    def build_csr_dataframe(self, files_per_entity):
        """Takes the complete data dictionary with all of the read input files. Merges the data per entity type and adds
         INDIVIDUAL_ID and DIAGNOSIS_ID to the biomaterial entity. Data duplication is taken care of within entities

         Returns the complete central subject registry as a
         pandas Dataframe using pandas concat()

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
            if not files_per_entity[entity]:
                logger.error('Missing data for entity: {} does not have a corresponding file.'.format(entity))
                missing_entities = True
                continue

            if entity == 'biomaterial' and 'biosource' in entity_to_data_frames.keys():
                for filename in files_per_entity[entity]:
                    files_per_entity[entity][filename] = add_biosource_identifiers(
                        entity_to_data_frames['biosource'], files_per_entity[entity][filename])

            logger.debug('Merging data for entity: {}'.format(entity))
            df = merge_entity_data_frames(df_dict=files_per_entity[entity],
                                          id_columns=columns,
                                          name=entity)
            entity_to_data_frames[entity] = df

        if missing_entities:
            logger.error('Missing data for one or more entities, cannot continue.')
            raise DataException()

        # TODO: ADD DEDUPLICATION ACROSS ENTITIES:
        # TODO: Add advanced deduplication for double values from for example individual and diagnosis.
        # TODO: idea to capture this in a config file where per column for the CSR the main source is described.
        # TODO: This could reuse the file_header mapping to create subselections and see if there are duplicates.
        # TODO: The only thing that is not covered is some edge cases where a data point from X should lead instead of
        # TODO: the normal Y data point.

        # Concat all data starting with individual into the CSR dataframe, study, diagnosis, biosource and biomaterial
        subject_registry = pd.concat(entity_to_data_frames.values())

        return subject_registry, entity_to_data_frames

    def read_data_files(self):
        """Loop over the clinical_data_dir and process all the clinical data.
        Check if all expected files and headers are in the input data and remap the input columns to the expected
        Central Subject Registry(CSR) column headers.

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

        files_found = {filename: False for filename in self.expected_files}

        clinical_files = get_filelist(self.input_dir)

        date_errors = []
        incorrect_files = []
        file_type_error = False
        codebook_mapping_error = []
        for file in clinical_files:
            filename = os.path.basename(file)

            if filename in files_found:
                files_found[filename] = True

            validate_error = validate_source_file(self.file_prop_dict, file)
            if validate_error:
                exit_after_process.append(file)
                continue

            # Check if codebook is available for filename, if not codebook will be None
            codebook = check_for_codebook(filename, self.output_dir)

            # Read data from file and create a pandas DataFrame. If a header mapping is provided the columns
            # are mapped before the DataFrame is returned
            df, mapping_status = input_file_to_df(filename=file, encoding=get_encoding(file), codebook=codebook)
            if not mapping_status:
                codebook_mapping_error.append(file)

            # Update date format
            date_errors.append(set_date_fields(df, self.file_prop_dict, filename))

            # Check if mapping for columns to CSR fields is present
            header_map = self.columns_to_csr_map[filename] if filename in self.columns_to_csr_map else None
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
            logger.error(
                'Validation failed for the following files {}. Look at the error messages above for more detailed '
                'information.'.format(exit_after_process))

        if file_type_error:
            logger.error('Could not determine file types for {}, missing identifying keys. Please add one of the '
                         'identifying keys {}'.format(incorrect_files, ST_COLUMNS.update(PK_COLUMNS)))

        # if any of the errors are found the program should exit
        if len(exit_after_process) > 0 or any(date_errors) or file_type_error or codebook_mapping_error:
            raise DataException()

        missing_expected_files = check_file_list(files_found)
        if missing_expected_files:
            logger.error('Missing expected files. For more information see errors above')
            raise DataException()

        return files_per_entity

    def read_subject_data(self) -> Tuple[Any, CentralSubjectRegistry]:

        # Read in the data files per entity
        files_per_entity = self.read_data_files()

        # Use read in data to build the Central Subject Registry
        subject_registry_df, entity_to_data_frames = self.build_csr_dataframe(files_per_entity)

        logger.info('Subject registry built')

        subject_registry_df = self.resolve_data_conflicts(subject_registry_df)

        subject_registry_df = calculate_helper_variables(subject_registry_df, self.input_dir)

        # Drop columns from the subject registry that are captured in the study registry
        columns_to_drop = {col for col_list in self.study_data_model.values()
                           for col in col_list if col not in PK_COLUMNS}
        subject_registry_df = subject_registry_df.drop(columns=columns_to_drop, errors='ignore')

        # Check if all fields expected in the CSR dataframe are present.
        # The expected columns are derived from the CSR data model
        csr_expected_header = []
        for key in self.csr_data_model:
            csr_expected_header += list(self.csr_data_model[key])
        missing_header = [l for l in csr_expected_header if l not in subject_registry_df.columns]
        if len(missing_header) > 0:
            logger.warning('Missing columns from Central Subject Registry data model: {}'.format(missing_header))
            # sys.exit(1) #Should this exit?

        if pd.isnull(subject_registry_df['INDIVIDUAL_ID']).any():
            # TODO extend error message here to include pointers to files?
            logger.error('Found data rows with no individual or patient identifier')
            raise DataException()

        individuals = transform_entities(
            entity_to_data_frames['individual'],
            Individual.schema(),
            lambda entity: Individual(**entity)
        )
        subject_registry = CentralSubjectRegistry(individuals=individuals)
        subject_registry.diagnoses = transform_entities(
            entity_to_data_frames['diagnosis'],
            Diagnosis.schema(),
            lambda entity: Diagnosis(**entity)
        )
        subject_registry.biosources = transform_entities(
            entity_to_data_frames['biosource'],
            Biosource.schema(),
            lambda entity: Biosource(**entity)
        )
        subject_registry.biomaterials = transform_entities(
            entity_to_data_frames['biomaterial'],
            Biomaterial.schema(),
            lambda entity: Biomaterial(**entity)
        )

        return subject_registry_df, subject_registry

    def read_study_data(self) -> Tuple[Any, StudyRegistry]:
        # Read in the data files per entity
        files_per_entity = self.read_data_files()

        study_registry_df, study_df, individual_study_df =\
            build_study_registry(study=files_per_entity.pop('study'),
                                 ind_study=files_per_entity.pop('individual_study'),
                                 csr_data_model=self.study_data_model)

        logger.info('Study registry built')

        study_registry = StudyRegistry()
        study_registry.studies = transform_entities(
            study_df, Study.schema(), lambda e: Study(**e))
        study_registry.individual_studies = transform_entities(
            individual_study_df, IndividualStudy.schema(), lambda e: IndividualStudy(**e))

        return study_registry_df, study_registry
