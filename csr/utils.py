from typing import List, Dict, Any

import pandas as pd

from csr.csr import CentralSubjectRegistry, Individual, Diagnosis, Biosource, Biomaterial, StudyRegistry, Study, \
    IndividualStudy


def read_subject_registry_from_tsv(input_file_dir) -> CentralSubjectRegistry:
    try:
        individual_dicts = tsv_to_list_of_dicts('{}/{}'.format(input_file_dir, 'individual.tsv'))
        individuals = list(map(lambda i: Individual(**i), individual_dicts))

        diagnosis_dicts = tsv_to_list_of_dicts('{}/{}'.format(input_file_dir, 'diagnosis.tsv'))
        diagnoses = list(map(lambda i: Diagnosis(**i), diagnosis_dicts))

        biosource_dicts = tsv_to_list_of_dicts('{}/{}'.format(input_file_dir, 'biosource.tsv'))
        biosources = list(map(lambda i: Biosource(**i), biosource_dicts))

        biomaterial_dicts = tsv_to_list_of_dicts('{}/{}'.format(input_file_dir, 'biomaterial.tsv'))
        biomaterials = list(map(lambda i: Biomaterial(**i), biomaterial_dicts))

        return CentralSubjectRegistry(individuals=individuals,
                                      diagnoses=diagnoses,
                                      biosources=biosources,
                                      biomaterials=biomaterials)
    except FileNotFoundError as fnfe:
        raise FileNotFoundError('File not found. {}'.format(fnfe))


def read_study_registry_from_tsv(input_file_dir) -> StudyRegistry:
    try:
        study_dicts = tsv_to_list_of_dicts('{}/{}'.format(input_file_dir, 'study.tsv'))
        studies = list(map(lambda i: Study(**i), study_dicts))

        individual_study_dicts = tsv_to_list_of_dicts('{}/{}'.format(input_file_dir, 'individual_study.tsv'))
        individual_studies = list(map(lambda i: IndividualStudy(**i), individual_study_dicts))

        return StudyRegistry(studies=studies,
                             individual_studies=individual_studies)
    except FileNotFoundError as fnfe:
        raise FileNotFoundError('File not found. {}'.format(fnfe))


def tsv_to_list_of_dicts(file_name: str) -> List[Dict[str, Any]]:
    values_df = pd.read_csv(file_name, sep='\t')
    return values_df.to_dict('records')

