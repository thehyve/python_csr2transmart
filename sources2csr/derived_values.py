from collections import defaultdict
from typing import List, Dict, Set

from dateutil.relativedelta import relativedelta

from csr.csr import CentralSubjectRegistry, Diagnosis
from sources2csr.ngs import NGS


def add_derived_values(subject_registry: CentralSubjectRegistry, ngs_set: Set[NGS]) -> CentralSubjectRegistry:
    """

    :param ngs_set:
    :param subject_registry:
    :return:
    """

    # Collect relevant diagnosis aggregates per individual
    diagnoses_per_individual: Dict[str, List[Diagnosis]] = defaultdict(list)
    for diagnosis in subject_registry.diagnoses:
        diagnoses_per_individual[diagnosis.individual_id].append(diagnosis)
    diagnosis_count_per_individual = {}
    first_diagnosis_date_per_individual = {}
    for individual_id, diagnoses in diagnoses_per_individual.items():
        diagnosis_count_per_individual[individual_id] = len(diagnoses)
        diagnosis_dates = [d.diagnosis_date for d in diagnoses if d.diagnosis_date is not None]
        if len(diagnosis_dates) > 0:
            first_diagnosis_date = sorted(diagnosis_dates)[0]
            first_diagnosis_date_per_individual[individual_id] = first_diagnosis_date

    # Add diagnosis aggregates to individuals
    for individual in subject_registry.individuals:
        # Add diagnosis count
        individual.diagnosis_count = diagnosis_count_per_individual.get(individual.individual_id, None)
        # Add age at first diagnosis
        if individual.birth_date is not None:
            first_diagnosis_date = first_diagnosis_date_per_individual.get(individual.individual_id, None)
            if first_diagnosis_date is not None:
                individual.age_first_diagnosis = relativedelta(first_diagnosis_date, individual.birth_date).years

    # Add library_strategy aggregates and analysis_type to biomaterials
    if subject_registry.biomaterials and len(ngs_set) > 0:
        for biomaterial in subject_registry.biomaterials:
            for ngs in ngs_set:
                if biomaterial.biomaterial_id == ngs.biomaterial_id and \
                   biomaterial.src_biosource_id == ngs.biosource_id:
                    if ngs.analysis_type is not None:
                        biomaterial.analysis_type.append(ngs.analysis_type.value)
                    biomaterial.library_strategy.append(ngs.library_strategy.value)

    return subject_registry
