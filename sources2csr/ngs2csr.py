import logging
import os
from typing import Set

from csr.csr import CentralSubjectRegistry
from sources2csr.ngs import NGS
from sources2csr.ngs_maf_reader import NgsMafReader
from sources2csr.ngs_reader import NgsReader
from sources2csr.ngs_seg_reader import NgsSegReader
from sources2csr.ngs_txt_reader import NgsTxtReader


logger = logging.getLogger(__name__)


def read_ngs_files(ngs_dir: str) -> Set[NGS]:
    """ Reads NGS files inside input_dir in 3 different formats: `.txt`, `.maf.gz` and `.seg`.

    :param ngs_dir: NGS files directory
    :return: Set of NGS objects
    """
    ngs_data = set()
    txt_reader = NgsTxtReader(ngs_dir)
    maf_reader = NgsMafReader(ngs_dir)
    seg_reader = NgsSegReader(ngs_dir)

    for filename in NgsReader.list_files(ngs_dir):
        # logger.debug('Parsing {} data file from {}'.format(filename, directory))
        if filename.endswith('maf.gz'):
            ngs_data |= set(maf_reader.read_data(filename))
        if filename.endswith('seg'):
            ngs_data |= set(seg_reader.read_data(filename))
        elif filename.endswith('_all_data_by_genes.txt') or filename.endswith('_all_thresholded.by_genes.txt'):
            ngs_data |= set(txt_reader.read_data(filename))
    return ngs_data


def read_ngs_data(input_dir: str) -> Set[NGS]:
    ngs_dir = os.path.join(input_dir, 'NGS')
    if not os.path.isdir(ngs_dir):
        logger.info('No NGS data found.')
        return set()
    logger.info('Reading NGS data.')
    return read_ngs_files(ngs_dir)


def add_ngs_data(subject_registry: CentralSubjectRegistry, input_dir: str) -> CentralSubjectRegistry:
    """Add library_strategy aggregates and analysis_type to biomaterials based on the NGS data
    :param subject_registry: Central Subject Registry
    :param input_dir: input directory that contains the directory with NGS input files
    :return: updated Central Subject Registry
    """
    ngs_data = read_ngs_data(input_dir)
    if subject_registry.entity_data['Biomaterial'] and ngs_data:
        for biomaterial in subject_registry.entity_data['Biomaterial']:
            biomaterial.analysis_type = []
            biomaterial.library_strategy = []
            for ngs in ngs_data:
                if biomaterial.biomaterial_id == ngs.biomaterial_id and \
                   biomaterial.src_biosource_id == ngs.biosource_id:
                    if ngs.analysis_type is not None:
                        biomaterial.analysis_type.append(ngs.analysis_type.value)
                    biomaterial.library_strategy.append(ngs.library_strategy.value)
    return subject_registry
