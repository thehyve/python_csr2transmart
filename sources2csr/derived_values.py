from collections import defaultdict
from typing import List, Dict, Sequence
from dateutil.relativedelta import relativedelta

from csr.csr import CentralSubjectRegistry, Diagnosis


def add_derived_values(subject_registry: CentralSubjectRegistry) -> CentralSubjectRegistry:
    """Compute derived diagnosis aggregate values
    :param subject_registry: Central Subject Registry
    :return: updated Central Subject Registry
    """

    # Collect relevant diagnosis aggregates per individual
    # Step 1: Create dictionary with individual id as key and list of diagnosis objects as value
    diagnoses_per_individual: Dict[str, List[Diagnosis]] = defaultdict(list)
    diagnosis_data: Sequence[Diagnosis] = subject_registry.entity_data['Diagnosis']
    for diagnosis in diagnosis_data:
        diagnoses_per_individual[diagnosis.individual_id].append(diagnosis)
    # Step 2: Collect per individual the number of diagnosis and the age when they first received a diagnosis ID.
    diagnosis_count_per_individual = {}
    first_diagnosis_age_per_individual = {}
    for individual_id, diagnoses in diagnoses_per_individual.items():
        diagnosis_count_per_individual[individual_id] = len(diagnoses)
        diagnosis_ages = [d.age_at_diagnosis for d in diagnoses if d.age_at_diagnosis is not None]
        if diagnosis_ages:
            first_diagnosis_age = sorted(diagnosis_ages)[0]
            first_diagnosis_age_per_individual[individual_id] = first_diagnosis_age

    # Step 3: Fill in the missing diagnosis count and first age at diagnosis values
    # Add diagnosis aggregates to individuals
    for individual in subject_registry.entity_data['Individual']:
        # Add diagnosis count
        if individual.diagnosis_count is None:
            individual.diagnosis_count = diagnosis_count_per_individual.get(individual.individual_id, None)
        # Add age at first diagnosis
        if individual.age_first_diagnosis is None:
            individual.age_first_diagnosis = first_diagnosis_age_per_individual.get(individual.individual_id, None)

    return subject_registry
