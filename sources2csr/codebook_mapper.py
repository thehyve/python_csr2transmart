from typing import Any, Dict, List, Optional, Sequence

from csr.exceptions import DataException
from sources2csr.codebook import CodeBook, ColumnValueMapping


def read_codebook(codebook_filename: str) -> CodeBook:
    """Process the content of a codebook and return the reformatted codebook as an object.
    Expected import format is a tab-delimited file.

    Format:
    - A header line is followed by one or more value mapping lines.
    - Header lines contain two columns: a number and a space separated list of column names. E.g., "1\tSEX GENDER".
    - Value mapping lines start with an empty field, followed by code, value pairs. E.g., "\t1\tMale\t2\tFemale".

    :param codebook_filename: file name of the code book
    :return: code book object
    """
    with open(codebook_filename, 'r') as code_book_file:
        column_mappings: Dict[str, ColumnValueMapping] = {}
        current_value_mapping: Dict[Any, Any] = {}
        current_columns: Optional[List[str]] = None
        line_number = 0
        for line in code_book_file:
            line_number += 1
            line = line.strip('\n')
            if not line.startswith('\t'):
                # Save previous column mapping
                if current_columns is not None:
                    column_value_mapping = ColumnValueMapping(value_mapping=current_value_mapping)
                    for column in current_columns:
                        column_mappings[column] = column_value_mapping
                # Start new column mapping
                tokens = line.split('\t')
                if len(tokens) < 2:
                    raise DataException(
                        f'Invalid header in codebook {codebook_filename} on line {line_number}')
                current_columns = [column_name.lower() for column_name in tokens[1].split(' ')]
                duplicate_columns = set(current_columns).intersection(column_mappings.keys())
                if duplicate_columns:
                    raise DataException(
                        f'Duplicate columns in codebook on line {line_number}: {", ".join(duplicate_columns)}')
                current_value_mapping = {}
            else:
                # Add values to current value mapping
                tokens = line.split('\t')[1:]
                if len(tokens) % 2 != 0:
                    raise DataException(
                        f'Invalid value mapping in codebook {codebook_filename} on line {line_number}')
                it = iter(tokens)
                for code, value in zip(it, it):
                    if code != '' and value != '':
                        value = value.replace('"', '')
                        if code in current_value_mapping:
                            raise DataException(f'Duplicate code in codebook on line {line_number}: {code}')
                        current_value_mapping[code] = value
        # Save last column mapping
        if current_columns is not None:
            column_value_mapping = ColumnValueMapping(value_mapping=current_value_mapping)
            for column in current_columns:
                column_mappings[column] = column_value_mapping
        return CodeBook(column_mappings=column_mappings)


def apply_codebook_mapping(mapping: Dict[str, ColumnValueMapping], column: str, value: Any) -> Any:
    column_mapping = mapping.get(column.lower(), None)
    if column_mapping is None:
        return value
    return column_mapping.value_mapping.get(value, value)


class CodeBookMapper:

    def __init__(self, codebook_filename: str):
        self.codebook = read_codebook(codebook_filename)

    def apply(self, data: Sequence[Dict[str, Any]]) -> Sequence[Dict[str, Any]]:
        column_mappings = self.codebook.column_mappings
        data = [{k: apply_codebook_mapping(column_mappings, k, v) for k, v in item.items()} for item in data]
        return data
