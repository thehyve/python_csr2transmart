#!/usr/bin/env python3

# Code to create case lists
# Author: Sander Tan, The Hyve

import os
import logging

logger = logging.getLogger(__name__)
logger.name = logger.name.rsplit('.', 1)[1]


def create_caselist(output_dir,
                    file_name,
                    cancer_study_identifier=None,
                    stable_id=None,
                    case_list_name=None,
                    case_list_description=None,
                    case_list_category=None,
                    case_list_ids=None
                    ):

    # Define output directory
    case_list_dir = os.path.join(output_dir, 'case_lists')
    if not os.path.exists(case_list_dir):
        os.mkdir(case_list_dir)

    # Create contents
    caselist_content = ['cancer_study_identifier: {}'.format(cancer_study_identifier),
                        'stable_id: {}'.format(stable_id),
                        'case_list_name: {}'.format(case_list_name),
                        'case_list_description: {}'.format(case_list_description),
                        'case_list_category: {}'.format(case_list_category),
                        'case_list_ids: {}'.format(case_list_ids)
                        ]

    # Write file
    logger.debug('Writing cBioPortal caselist to {} for study {}'.format(file_name, cancer_study_identifier))
    with open(os.path.join(case_list_dir, file_name), 'w') as caselist_output_file:
        caselist_output_file.write('\n'.join(caselist_content) + '\n')
    return
