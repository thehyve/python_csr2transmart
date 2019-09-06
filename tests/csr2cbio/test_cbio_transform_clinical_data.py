import json
from collections import Counter

import pandas as pd
import pytest
from csr.csr import CentralSubjectRegistry
from csr.study_registry_reader import SubjectRegistryReader

from scripts.cbioportal_transformation.cbio_transform_clinical import \
    transform_patient_clinical_data, transform_sample_clinical_data


@pytest.fixture
def patient_clinical_data() -> pd.DataFrame:
    input_dir = './test_data/default_data'
    subject_registry_reader = SubjectRegistryReader(input_dir)
    subject_registry: CentralSubjectRegistry = subject_registry_reader.read_subject_registry()
    descriptions_file = './test_data/config/cbioportal_header_descriptions.json'
    with open(descriptions_file, 'r') as des:
        description_map = json.loads(des.read())
    return transform_patient_clinical_data(subject_registry, description_map)[0]


@pytest.fixture
def sample_clinical_data() -> pd.DataFrame:
    input_dir = './test_data/default_data'
    subject_registry_reader = SubjectRegistryReader(input_dir)
    subject_registry: CentralSubjectRegistry = subject_registry_reader.read_subject_registry()
    descriptions_file = './test_data/config/cbioportal_header_descriptions.json'
    with open(descriptions_file, 'r') as des:
        description_map = json.loads(des.read())
    return transform_sample_clinical_data(subject_registry, description_map)[0]


def test_patient_clinical_data(patient_clinical_data):
    assert len(patient_clinical_data) == 2
    assert list(patient_clinical_data.get('PATIENT_ID')) == ['PMCBS000BCA', 'PMCBM000BAB']
    assert Counter(list(patient_clinical_data)) == Counter(['PATIENT_ID', 'TAXONOMY', 'BIRTH_DATE', 'GENDER',
                                                            'IC_TYPE', 'IC_GIVEN_DATE',
                                                            'IC_WITHDRAWN_DATE', 'IC_MATERIAL', 'IC_DATA',
                                                            'IC_LINKING_EXT', 'REPORT_HER_SUSC', 'REPORT_INC_FINDINGS'])


def test_sample_clinical_data(sample_clinical_data):
    assert len(sample_clinical_data) == 4
    assert list(sample_clinical_data.get('SAMPLE_ID')) == ['PMCBS000AAA_PMCBM000AAA', 'PMCBS000AAB_PMCBM000AAB',
                                                           'PMCBS000AAC_PMCBM000AAC', 'PMCBS000AAD_PMCBM000AAD']
    assert Counter(list(sample_clinical_data)) == Counter(['ANALYSIS_TYPE', 'BIOMATERIAL_DATE', 'BIOMATERIAL_ID',
                                                           'BIOSOURCE_DATE', 'BIOSOURCE_DEDICATED', 'BIOSOURCE_ID',
                                                           'CENTER_TREATMENT', 'DIAGNOSIS_DATE', 'DIAGNOSIS_ID',
                                                           'DISEASE_STATUS', 'PATIENT_ID', 'LIBRARY_STRATEGY',
                                                           'SAMPLE_ID', 'SRC_BIOMATERIAL_ID', 'TISSUE', 'TOPOGRAPHY',
                                                           'TREATMENT_PROTOCOL', 'TUMOR_PERCENTAGE', 'TUMOR_STAGE',
                                                           'TUMOR_TYPE', 'TYPE', 'SRC_BIOSOURCE_ID'])
