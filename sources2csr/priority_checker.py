import logging

from sources2csr.csr_read_data import determine_file_type
from sources2csr.data_exception import DataException

ST_COLUMNS = {'STUDY_ID'}
PK_COLUMNS = {'INDIVIDUAL_ID', 'DIAGNOSIS_ID', 'BIOMATERIAL_ID', 'BIOSOURCE_ID'}


logger = logging.getLogger(__name__)


class PriorityChecker:
    """Checks the priority definition in column_priority.json for consistency with file_headers.json."""

    def __init__(self, file_prop_dict, columns_to_csr_map, column_prio_dict):
        self.file_prop_dict = file_prop_dict
        self.columns_to_csr_map = columns_to_csr_map
        self.column_prio_dict = column_prio_dict

    def get_study_files(self):
        exemption_set = set()
        for filename, file_items in self.file_prop_dict.items():
            item_list = []
            items = [i.upper() for i in file_items['headers']]
            if filename in self.columns_to_csr_map:
                for item in items:
                    item_list.append(self.columns_to_csr_map[filename].get(item, item))
            else:
                item_list = items

            if determine_file_type(item_list, filename) in ['study', 'individual_study']:
                exemption_set.add(filename)
        return exemption_set

    def get_overlapping_columns(self):
        """Determine which columns in the Central Subject Registry (CSR) have input from multiple files.
        Constructs a dict with conflicts grouped per CSR column.
        Takes two dicts which define expected headers in the input files
        and maps the expected headers to the CSR datamodel.

        :return: Dict with column names as keys and ordered filename lists as values.
        {CSR_COLUMN_NAME: [FILE_1, FILE_2]}
        """
        exemption_set = self.get_study_files()

        col_file_dict = dict()
        for filename in self.file_prop_dict:
            if filename in exemption_set:
                continue
            colname_dict = self.columns_to_csr_map[filename] if filename in self.columns_to_csr_map else None
            for colname in self.file_prop_dict[filename]['headers']:
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

    def check_column_prio(self):
        """Compare the priority definition from column_priority.json with what was found in file_headers.json and log
        all mismatches."""
        col_file_dict = self.get_overlapping_columns()
        found_error = False
        missing_in_priority = set(col_file_dict.keys()) - set(self.column_prio_dict.keys())
        missing_in_file_headers = set(self.column_prio_dict.keys()) - set(col_file_dict.keys())

        if missing_in_file_headers:
            for col in missing_in_file_headers:
                logger.warning(
                    'Priority is defined for column {0!r}, but the column was not found in the expected columns.'
                    ' Expected columns are defined in file_headers.json'.format(col))

        # Column name missing entirely
        if missing_in_priority:
            found_error = True
            for col in missing_in_priority:
                logger.error(
                    ('{0!r} column occurs in multiple data files: {1}, but no priority is '
                     'defined. Please specify the column priority in the column_priority.json file.').format(
                        col, col_file_dict[col]
                    )
                )

        # Priority present, but incomplete or unknown priority provided
        shared_columns = set(self.column_prio_dict.keys()).intersection(set(col_file_dict.keys()))
        for col in shared_columns:
            files_missing_in_prio = [
                filename for filename in col_file_dict[col] if filename not in self.column_prio_dict[col]]
            files_only_in_prio = [
                filename for filename in self.column_prio_dict[col] if filename not in col_file_dict[col]]
            if files_missing_in_prio:
                found_error = True
                logger.error((
                    'Incomplete priority provided for column {0!r}. It occurs in these files: {1}, but '
                    'priority found only for the following files: {2}. Please add the missing files {3} to the '
                    'priority mapping: column_priority.json for column: {0}').format(
                    col,
                    col_file_dict[col],
                    self.column_prio_dict[col],
                    list(set(col_file_dict[col]).difference(set(self.column_prio_dict[col]))))
                )

            if files_only_in_prio:
                logger.warning(('Provided priority for column {0!r} contains more files than present in '
                                'column_priority.json. The following priority files are not used: {1}').format(
                    col, files_only_in_prio)
                )

        if found_error:
            raise DataException()
