import os
from typing import Optional, Sequence, Dict, List

from csr.exceptions import ReaderException
from sources2csr.ngs import AnalysisType, NGS, LibraryStrategy


class NgsReader:
    """Reader that reads NGS data files.
    """
    def __init__(self, input_dir: str, library_strategy: LibraryStrategy):
        self.input_dir = input_dir
        self.library_strategy = library_strategy

    @staticmethod
    def determine_analysis_type(filename: str) -> Optional[AnalysisType]:
        """Determine whole genome or whole exome sequencing analysis type based on the filename.
        If _WGS or _WXS are not in the filename returns None.

        :param filename: name of the input file
        :return: Type of sequencing event
        """
        if '_WGS' in filename.upper():
            return AnalysisType.WGS
        elif '_WXS' in filename.upper():
            return AnalysisType.WXS
        else:
            return None

    @staticmethod
    def biosource_biomaterial_from_sample_id(sample_id: str, filename: str, by='_') -> tuple:
        """ Splits sample _id into biosource_id and biomaterial_id.
        Every sample ID should be structured as <BiosourceID>_<BiomaterialID>,
        e.g. PMCBS000AAA_PMCBM000AAA.

        :param sample_id: cBioPortal sample ID
        :param filename: ull path with a name of the input file
        :param by: Character to use for splitting, default: '_'
        :return: biosource_id and biomaterial_id values tuple or NgsReaderException
        """

        biosource_biomaterial_pair = sample_id.split(by)
        if len(biosource_biomaterial_pair) != 2:
            raise ReaderException('Invalid sample_id format found in {} NGS file. sample_id: {}'
                                  .format(filename, sample_id))
        else:
            return biosource_biomaterial_pair[0], biosource_biomaterial_pair[1]

    @staticmethod
    def list_files(input_dir: str) -> List[str]:
        """ Get list of file names inside a directory
        :param input_dir: directory with input files
        :return: List of file paths with names
        """
        for file in os.listdir(input_dir):
            if os.path.isfile(os.path.join(input_dir, file)):
                yield file

    def map_ngs(self, biosources_biomaterials_dict: Dict[str, Sequence[str]], filename: str) -> Optional[Sequence[NGS]]:
        """ Maps biosource to biomaterials dictionary to the NGS Sequence

        :param biosources_biomaterials_dict: biosource to biomaterials dictionary
        :param filename: name of the input file
        :return:
        """
        ngs_data = []
        analysis_type = self.determine_analysis_type(filename)
        for biosource, biomaterials in biosources_biomaterials_dict.items():
            for biomaterial in biomaterials:
                ngs_data.append(NGS(biosource_id=biosource,
                                    biomaterial_id=biomaterial,
                                    analysis_type=analysis_type,
                                    library_strategy=self.library_strategy))
        return ngs_data

    def read_data(self, filename: str) -> Optional[Sequence[NGS]]:
        pass
