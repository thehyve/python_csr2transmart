import csv
import gzip
import os
from typing import Sequence, Dict, Any

from csr.exceptions import ReaderException


class TabularFileReader:
    """
    Delimiter-separated values reader.
    """
    def __iter__(self):
        return self.reader.__iter__()

    def read_data(self) -> Sequence[Dict[str, Any]]:
        data = []
        first = True
        header = None
        line_num = 0
        for line in self:
            line_num += 1
            if line and str.startswith(line[0], '#'):
                # skip comment lines
                continue
            if first:
                header = line
                first = False
            else:
                if not len(line) == len(header):
                    raise ReaderException(f'Unexpected line length {len(line)}. Expected {len(header)}. '
                                          f'File {self.path}, line number: {line_num}.')
                record = dict([(header[i], line[i]) for i in range(0, len(header))])
                data.append(record)
        return data

    def close(self) -> None:
        if self.file:
            self.file.close()

    def __init__(self, path: str, delimiter='\t'):
        self.file = None
        self.path = path
        if not os.path.isfile(path):
            raise ReaderException(f'File not found: {path}')
        if str.endswith(path, '.gz'):
            self.file = gzip.open(path, 'rt')
        else:
            self.file = open(path, 'r')
        self.reader = csv.reader(self.file, delimiter=delimiter)

    def __del__(self):
        self.close()
