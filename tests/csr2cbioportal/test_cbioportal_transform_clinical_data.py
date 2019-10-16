from collections import Counter

import pandas as pd
import pytest
from csr.csr import CentralSubjectRegistry
from csr.subject_registry_reader import SubjectRegistryReader
from csr2cbioportal.transform_clinical import transform_patient_clinical_data, transform_sample_clinical_data


@pytest.fixture
def patient_clinical_data() -> pd.DataFrame:
    input_dir = './test_data/input_data/CSR2CBIOPORTAL_TEST_DATA'
    subject_registry_reader = SubjectRegistryReader(input_dir)
    subject_registry: CentralSubjectRegistry = subject_registry_reader.read_subject_registry()
    return transform_patient_clinical_data(subject_registry)[0]


@pytest.fixture
def sample_clinical_data() -> pd.DataFrame:
    input_dir = './test_data/input_data/CSR2CBIOPORTAL_TEST_DATA'
    subject_registry_reader = SubjectRegistryReader(input_dir)
    subject_registry: CentralSubjectRegistry = subject_registry_reader.read_subject_registry()
    return transform_sample_clinical_data(subject_registry)[0]


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
                                                           'PMCBS000AAB_PMCBM000AAC', 'PMCBS000AAD_PMCBM000AAD']
    assert Counter(list(sample_clinical_data)) == Counter(['BIOMATERIAL_DATE', 'BIOMATERIAL_ID',
                                                           'BIOSOURCE_DATE', 'BIOSOURCE_DEDICATED', 'BIOSOURCE_ID',
                                                           'CENTER_TREATMENT', 'DIAGNOSIS_DATE', 'DIAGNOSIS_ID',
                                                           'DISEASE_STATUS', 'PATIENT_ID',
                                                           'SAMPLE_ID', 'SRC_BIOMATERIAL_ID', 'TISSUE', 'TOPOGRAPHY',
                                                           'TREATMENT_PROTOCOL', 'TUMOR_PERCENTAGE', 'TUMOR_STAGE',
                                                           'TUMOR_TYPE', 'TYPE', 'SRC_BIOSOURCE_ID'])
