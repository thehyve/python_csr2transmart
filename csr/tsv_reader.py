import csv
from typing import Sequence, Dict, Any


class TsvReaderException(Exception):
    pass


class TsvReader:
    """
    Tab-separated values reader.
    """
    def __iter__(self):
        return self.reader.__iter__()

    def read_data(self) -> Sequence[Dict[str, Any]]:
        data = []
        first = True
        header = None
        for line in self:
            if first:
                header = line
                first = False
            else:
                if not len(line) == len(header):
                    raise TsvReaderException(f'Unexpected line length {len(line)}. Expected {len(header)}')
                record = dict([(header[i], line[i]) for i in range(0, len(header))])
                data.append(record)
        return data

    def close(self) -> None:
        if self.file:
            self.file.close()

    def __init__(self, path: str):
        self.file = open(path, 'r')
        self.reader = csv.reader(self.file, delimiter='\t')

    def __del__(self):
        self.close()
