import os
from typing import Optional, Sequence

from csr.tabular_file_reader import TabularFileReader
from sources2csr.ngs import NGS, LibraryStrategy
from sources2csr.ngs_reader import NgsReader, ReaderException


class NgsSegReader(NgsReader):
    """ Segment data reader.
        Parses NGS files with the '.seg' extension as a tab-separated text.
    """

    def __init__(self, input_dir: str):
        super().__init__(input_dir, LibraryStrategy.CNV)

    def read_data(self, filename: str) -> Optional[Sequence[NGS]]:
        """ Reads .seg file as tab separated file.
        Sample ID should be specified in the first column.

        :param filename: name of the input file
        :return: Sequence of NGS objects
        """
        data = TabularFileReader(os.path.join(self.input_dir, filename)).read_data()
        biosource_biomaterial_dict = dict()
        if len(data) > 1:
            for row in data:
                sample_id = list(row.values())[0]
                biosource_biomaterial = self.biosource_biomaterial_from_sample_id(sample_id, filename)
                biosource_biomaterial_dict.setdefault(biosource_biomaterial[0], []).append(biosource_biomaterial[1])
        else:
            raise ReaderException("Cannot read NGS data from file: {}. Empty data.".format(filename))
        return self.map_ngs(biosource_biomaterial_dict, filename)
