import os
from typing import Optional, Sequence

from csr.tabular_file_reader import TabularFileReader
from sources2csr.ngs import NGS, LibraryStrategy
from sources2csr.ngs_reader import NgsReader, ReaderException


class NgsTxtReader(NgsReader):
    """ Reads .txt files with Continuous CNA per gene and Discrete CNA per gene data.
    """

    def __init__(self, input_dir: str):
        super().__init__(input_dir, LibraryStrategy.CNV)

    def read_data(self, filename: str) -> Optional[Sequence[NGS]]:
        """ Reads .txt file.
        Sample_id should be specified in the header.
        Assumes that all column names except Gene Symbol, Gene ID, Locus ID and Cytoband
        are sample identifiers.

        :param filename: name of the input file
        :return: Sequence of NGS objects
        """
        data = TabularFileReader(os.path.join(self.input_dir, filename)).read_data()
        biosource_biomaterial_dict = dict()
        if data:
            sample_id_col_num = 0
            for col_value in data[0]:
                if col_value not in ['Gene Symbol', 'Gene ID', 'Locus ID', 'Cytoband']:
                    sample_id_col_num += 1
                    biosource_biomaterial = self.biosource_biomaterial_from_sample_id(col_value, filename)
                    biosource_biomaterial_dict.setdefault(biosource_biomaterial[0], []).append(biosource_biomaterial[1])
            if sample_id_col_num == 0:
                raise ReaderException("Cannot read NGS data from file: {}. No sample_id found in header"
                                      .format(filename))
        else:
            raise ReaderException("Cannot read NGS data from file: {}. Empty data.".format(filename))
        return self.map_ngs(biosource_biomaterial_dict, filename)
