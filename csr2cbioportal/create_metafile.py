#!/usr/bin/env python3

# Code to create meta files
# Author: Sander Tan, The Hyve

import sys
import logging

logger = logging.getLogger(__name__)
logger.name = logger.name.rsplit('.', 1)[1]
sys.dont_write_bytecode = True


def create_meta_content(file_name,
                        cancer_study_identifier=None,
                        genetic_alteration_type=None,
                        datatype=None,
                        data_filename=None,
                        stable_id=None,
                        profile_name=None,
                        profile_description=None,
                        show_profile_in_analysis_tab=None,
                        type_of_cancer=None,
                        name=None,
                        short_name=None,
                        description=None,
                        add_global_case_list=None,
                        variant_classification_filter=None,
                        pmid=None,
                        reference_genome_id=None,
                        swissprot_identifier=None
                        ):

    # Required properties
    meta_content = []
    if cancer_study_identifier is not None:
        meta_content.append('cancer_study_identifier: {}'.format(cancer_study_identifier))

    # Properties that are required for most data types
    if genetic_alteration_type is not None:
        meta_content.append('genetic_alteration_type: {}'.format(genetic_alteration_type))
        meta_content.append('datatype: {}'.format(datatype))
        meta_content.append('data_filename: {}'.format(data_filename))

    # Properties that are required for mutation, gene expression and protein enrichment profiles
    if stable_id is not None:
        meta_content.append('stable_id: {}'.format(stable_id))
        meta_content.append('profile_name: {}'.format(profile_name))
        meta_content.append('profile_description: {}'.format(profile_description))
        meta_content.append('show_profile_in_analysis_tab: {}'.format(show_profile_in_analysis_tab))

    # Properties that are required for meta_study
    if name is not None:
        meta_content.append('type_of_cancer: {}'.format(type_of_cancer))
        meta_content.append('name: {}'.format(name))
        meta_content.append('short_name: {}'.format(short_name))
        meta_content.append('description: {}'.format(description))
        meta_content.append('add_global_case_list: {}'.format(add_global_case_list))

    if variant_classification_filter is not None:
        meta_content.append('variant_classification_filter: {}'.format(variant_classification_filter))

    if swissprot_identifier is not None:
        meta_content.append('swissprot_identifier: {}'.format(swissprot_identifier))

    if pmid is not None:
        meta_content.append('pmid: {}'.format(pmid))

    if reference_genome_id is not None:
        meta_content.append('reference_genome_id: {}'.format(reference_genome_id))
        meta_content.append('description: {}'.format(description))

    # Write file
    logger.debug('Writing cBioPortal metadata to {} for study {} and datatype {}'
                 .format(file_name, cancer_study_identifier, datatype))
    with open(file_name, 'w') as meta_output_file:
        meta_output_file.write('\n'.join(meta_content) + '\n')
    return
