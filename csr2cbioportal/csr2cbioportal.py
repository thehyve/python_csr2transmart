#!/usr/bin/env python3

# Code to transform PMC processed data to cBioPortal staging files
# Author: Sander Tan, The Hyve

import csv
import errno
import gzip
import logging
import os
import shutil
import sys
import time
from typing import List, Set, Optional

import click
import pandas as pd
from csr.logging import setup_logging

from csr.csr import CentralSubjectRegistry
from csr.exceptions import DataException
from csr.subject_registry_reader import SubjectRegistryReader
from .create_caselist import create_caselist
from .create_metafile import create_meta_content
from .transform_clinical import write_clinical, transform_patient_clinical_data, transform_sample_clinical_data

logger = logging.getLogger(__name__)

# Define study properties
STUDY_ID = 'csr'
NAME = "Central Subject Registry"
NAME_SHORT = "Central Subject Registry"
DESCRIPTION = 'Transformed to cBioPortal format on: %s' % time.strftime("%d-%m-%Y %H:%M")
TYPE_OF_CANCER = 'mixed'


def prepare_output_directory(output_dir: str):
    # Remove old output directory and recreate to ensure all NGS data is
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    try:
        os.makedirs(output_dir, exist_ok=False)
    except OSError as oe:
        # Catch the error if the folder already exists as this indicates shutil.rmtree did something wrong
        if oe.errno == errno.EEXIST:
            logger.error('Failed to create the output directory {} as it already exists.\
             It was not cleared successfully, Error {}'.format(output_dir, oe))
        raise oe


def process_clinical_data(input_dir: str, output_dir: str) -> List[str]:
    """
    Reads subject registry data from input_dir and transforms the data
    to clinical data files for cBioPortal.
    Writes the generated data files to output_dir.
    Returns the list of sample identifiers in the clinical data.
    """
    # Clinical data
    subject_registry_reader = SubjectRegistryReader(input_dir)
    subject_registry: CentralSubjectRegistry = subject_registry_reader.read_subject_registry()

    # Transform patient file
    patient_clinical_data, patient_clinical_header = transform_patient_clinical_data(subject_registry)
    write_clinical(patient_clinical_data, patient_clinical_header, 'patient', output_dir, STUDY_ID)

    # Transform sample file
    sample_clinical_data, sample_clinical_header = transform_sample_clinical_data(subject_registry)
    write_clinical(sample_clinical_data, sample_clinical_header, 'sample', output_dir, STUDY_ID)

    return sample_clinical_data['SAMPLE_ID'].unique().tolist()


def process_mutation_data(ngs_dir: str, output_dir: str, clinical_sample_ids: List[str]) -> Set[str]:
    """
    Reads data from all MAF files in ngs_dir and creates a combined mutation data file
    and the meta and caselist files for the mutation data.

    Returns the list of sample identifiers found in the mutation data.
    An exception is raised when any of the sample identifiers is not in the clinical_sample_ids list.
    """
    mutation_samples = combine_maf(ngs_dir, os.path.join(output_dir, 'data_mutations.maf'))

    if mutation_samples:
        # Create meta file
        meta_filename = os.path.join(output_dir, 'meta_mutations.txt')
        create_meta_content(meta_filename, cancer_study_identifier=STUDY_ID,
                            genetic_alteration_type='MUTATION_EXTENDED', datatype='MAF',
                            stable_id='mutations', show_profile_in_analysis_tab='true',
                            profile_name='Mutations', profile_description='Mutation data',
                            data_filename='data_mutations.maf', variant_classification_filter='',
                            swissprot_identifier='accession')

        # Create case list
        create_caselist(output_dir=output_dir, file_name='cases_sequenced.txt',
                        cancer_study_identifier=STUDY_ID,
                        stable_id='%s_sequenced' % STUDY_ID, case_list_name='Sequenced samples',
                        case_list_description='All sequenced samples',
                        case_list_category='all_cases_with_mutation_data',
                        case_list_ids="\t".join(mutation_samples))

        # Test for samples in MAF files that are not in clinical data
        if not set(clinical_sample_ids).issuperset(mutation_samples):
            logger.error("Found samples in MAF files that are not in clinical data: {}".format(
                ", ".join(mutation_samples.difference(set(clinical_sample_ids)))))
            raise DataException('Found samples in MAF files that are not in clinical data')
    return mutation_samples


def process_cna_files(ngs_dir: str, output_dir: str, clinical_sample_ids: List[str]) -> List[str]:
    """
    Reads CNA data files (segmented, continuous and discrete) from ngs_dir, copies the files,
    drops and renames certain columns, and writes meta and case list files.

    Returns list of CNA sample identifiers.
    An exception is raised when any of the sample identifiers is not in the clinical_sample_ids list.
    """
    # Select all non-hidden files
    study_files = []
    for study_file in os.listdir(ngs_dir):
        if not study_file.startswith('.'):
            study_files.append(study_file)

    # Create sample list, required for cnaseq case list
    cna_samples = []

    # Transform CNA data files
    for study_file in study_files:
        if study_file.endswith('sha1'):
            continue

        # TODO to be removed after upgrade to cBioPortal version that supports hg38 for segment data
        # For now skipping upload of .seg files, see: https://github.com/thehyve/python_csr2transmart/issues/62
        cbioportal_seg_hg38_support = False

        # CNA Segment data
        if study_file.split('.')[-1] == 'seg' and cbioportal_seg_hg38_support:
            logger.debug('Transforming segment data: %s' % study_file)

            output_file = 'data_cna_segments.seg'

            # Read file and replace header
            with open(os.path.join(ngs_dir, study_file)) as segment_file:
                segment_lines = segment_file.readlines()
                segment_lines[0] = 'ID	chrom	loc.start	loc.end	num.mark	seg.mean\n'

            # Write a copy with replaced header
            with open(os.path.join(output_dir, output_file), 'w') as segment_file:
                segment_file.writelines(segment_lines)

            # Create meta file
            meta_filename = os.path.join(output_dir, 'meta_cna_segments.txt')
            create_meta_content(meta_filename, cancer_study_identifier=STUDY_ID,
                                genetic_alteration_type='COPY_NUMBER_ALTERATION', datatype='SEG',
                                reference_genome_id='hg38', description='Segment data', data_filename=output_file)

        # CNA Continuous
        elif 'data_by_genes' in study_file:
            logger.debug('Transforming continuous CNA data: %s' % study_file)

            output_file = 'data_cna_continuous.txt'

            # Read file
            cna_data = pd.read_csv(os.path.join(ngs_dir, study_file), sep='\t', na_values=[''], dtype={'Gene ID': str})
            # Remove column and rename column names
            cna_data.drop('Cytoband', axis=1, inplace=True)
            cna_data.rename(columns={'Gene Symbol': 'Hugo_Symbol', 'Gene ID': 'Entrez_Gene_Id'}, inplace=True)

            # Remove negative Entrez IDs. This can lead to incorrect mapping in cBioPortal
            for index, row in cna_data.iterrows():
                if int(row['Entrez_Gene_Id']) < -1:
                    cna_data.loc[index, 'Entrez_Gene_Id'] = ''
            cna_data.to_csv(os.path.join(output_dir, output_file), sep='\t', index=False, header=True)

            # Create meta file
            meta_filename = os.path.join(output_dir, 'meta_cna_continuous.txt')
            create_meta_content(meta_filename, cancer_study_identifier=STUDY_ID,
                                genetic_alteration_type='COPY_NUMBER_ALTERATION', datatype='LOG2-VALUE',
                                stable_id='log2CNA', show_profile_in_analysis_tab='false',
                                profile_name='Copy-number alteration values',
                                profile_description='Continuous copy-number alteration values for each gene.',
                                data_filename=output_file)

            # Create case list
            cna_samples = cna_data.columns[2:].tolist()
            create_caselist(output_dir=output_dir, file_name='cases_cna.txt', cancer_study_identifier=STUDY_ID,
                            stable_id='%s_cna' % STUDY_ID, case_list_name='CNA samples',
                            case_list_description='All CNA samples', case_list_category='all_cases_with_cna_data',
                            case_list_ids="\t".join(cna_samples))

            # Test for samples in CNA files that are not in clinical data
            if not set(clinical_sample_ids).issuperset(set(cna_samples)):
                logger.error("Found samples in CNA files that are not in clinical data: {}".format(
                    ", ".join(set(cna_samples).difference(set(clinical_sample_ids))))
                )
                raise DataException('Found samples in CNA files that are not in clinical data')

        # CNA Discrete
        elif 'thresholded.by_genes' in study_file:
            logger.debug('Transforming discrete CNA data: %s' % study_file)

            output_file = 'data_cna_discrete.txt'

            # Read input file
            cna_data = pd.read_csv(os.path.join(ngs_dir, study_file), sep='\t', na_values=[''], dtype={'Gene ID': str})
            # Remove column and rename column names
            cna_data.drop('Cytoband', axis=1, inplace=True)
            cna_data.rename(columns={'Gene Symbol': 'Hugo_Symbol', 'Locus ID': 'Entrez_Gene_Id'}, inplace=True)

            # Remove negative Entrez IDs. This can lead to incorrect mapping in cBioPortal
            for index, row in cna_data.iterrows():
                if int(row['Entrez_Gene_Id']) < -1:
                    cna_data.loc[index, 'Entrez_Gene_Id'] = ''
            cna_data.to_csv(os.path.join(output_dir, output_file), sep='\t', index=False, header=True)

            # Create meta file
            meta_filename = os.path.join(output_dir, 'meta_cna_discrete.txt')
            profile_description = 'Putative copy-number alteration values for each gene from GISTIC 2.0.' \
                                  'Values: -2 = homozygous deletion; -1 = hemizygous deletion;' \
                                  '0 = neutral / no change; 1 = gain; 2 = high level amplification.'

            create_meta_content(meta_filename, cancer_study_identifier=STUDY_ID,
                                genetic_alteration_type='COPY_NUMBER_ALTERATION', datatype='DISCRETE',
                                stable_id='gistic', show_profile_in_analysis_tab='true',
                                profile_name='Putative copy-number alterations from GISTIC',
                                profile_description=profile_description,
                                data_filename=output_file)
        elif study_file.split('.')[-2:] == ['maf', 'gz']:
            # Mutations file are transformed in an other loop
            pass

        else:
            logger.warning("Unknown file type: %s" % study_file)
    return cna_samples


def create_cbioportal_study(input_dir: str, ngs_dir: Optional[str], output_dir: str):
    prepare_output_directory(output_dir)

    logger.info('Reading clinical data: %s' % input_dir)
    clinical_sample_ids = process_clinical_data(input_dir, output_dir)

    if ngs_dir:
        logger.info('Reading NGS data: %s' % ngs_dir)
        mutation_samples = process_mutation_data(ngs_dir, output_dir, clinical_sample_ids)
        cna_samples = process_cna_files(ngs_dir, output_dir, clinical_sample_ids)

        # Create cnaseq case list
        cnaseq_samples = list(mutation_samples.union(cna_samples))
        if len(cnaseq_samples) > 0:
            create_caselist(output_dir=output_dir, file_name='cases_cnaseq.txt', cancer_study_identifier=STUDY_ID,
                            stable_id='%s_cnaseq' % STUDY_ID, case_list_name='Sequenced and CNA samples',
                            case_list_description='All sequenced and CNA samples',
                            case_list_category='all_cases_with_mutation_and_cna_data',
                            case_list_ids="\t".join(cnaseq_samples))

    # Create meta study file
    meta_filename = os.path.join(output_dir, 'meta_study.txt')
    create_meta_content(meta_filename, STUDY_ID, type_of_cancer=TYPE_OF_CANCER, name=NAME, short_name=NAME_SHORT,
                        description=DESCRIPTION, add_global_case_list='true')

    logger.info('Done transforming files for %s' % STUDY_ID)

    # Transformation completed
    logger.info('Transformation of studies complete.')
    return


def combine_maf(ngs_dir, output_file_location):
    """
    combines all found NGS files in one. It filters out variants without hugo symbol.
    :param ngs_dir: directory with NGS files
    :param output_file_location: the result NGS file
    :return: unique list of samples in the result file
    """
    samples = set()

    paths_to_process = get_paths_to_non_hidden_maf_gz_files(ngs_dir)

    if not paths_to_process:
        return samples

    header = get_complete_header(paths_to_process)

    if not header:
        return samples

    with open(output_file_location, 'w') as result_maf:
        writer = csv.DictWriter(result_maf, delimiter='\t', fieldnames=header)
        writer.writeheader()
        for study_file in paths_to_process:
            logger.debug('Processing NGS data file: {}'.format(study_file))
            with gzip.open(study_file, 'rt') as file:
                reader = csv.DictReader(not_commented_lines(file), delimiter='\t')
                for row in reader:
                    samples.add(row['Tumor_Sample_Barcode'])
                    writer.writerow(row)
        return samples


def not_commented_lines(iter):
    for line in iter:
        if not line.lstrip().startswith('#'):
            yield line


def get_paths_to_non_hidden_maf_gz_files(ngs_dir):
    paths_to_process = []
    for study_file in os.listdir(ngs_dir):
        if not study_file.startswith('.') and study_file.split('.')[-2:] == ['maf', 'gz']:
            paths_to_process.append(os.path.join(ngs_dir, study_file))
    return paths_to_process


def get_complete_header(paths_to_process):
    fieldnames = []
    for study_file in paths_to_process:
        with gzip.open(study_file, 'rt') as file:
            header = next(csv.reader(not_commented_lines(file), delimiter='\t'))
            for column in header:
                if column not in fieldnames:
                    fieldnames.append(column)
    return fieldnames


def csr2cbioportal(input_dir: str, ngs_dir: Optional[str], output_dir: str):
    logger.info('csr2cbioportal')
    try:
        create_cbioportal_study(input_dir, ngs_dir, output_dir)
    except Exception as e:
        logger.error(e)
        sys.exit(1)


@click.command()
@click.argument('input_dir', type=click.Path(file_okay=False, exists=True, readable=True))
@click.argument('output_dir', type=click.Path(file_okay=False, writable=True))
@click.option('--ngs-dir', type=click.Path(file_okay=False, exists=True, readable=True))
@click.option('--debug', is_flag=True, help='Print more verbose messages')
@click.version_option()
def run(input_dir, ngs_dir, output_dir, debug: bool):
    setup_logging(debug)
    csr2cbioportal(input_dir, ngs_dir, output_dir)


def main():
    run()


if __name__ == '__main__':
    main()
