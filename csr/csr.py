from datetime import date
from typing import Sequence, Optional, Union, Dict, List

from pydantic import BaseModel, Schema


class Individual(BaseModel):
    """
    Individual entity
    """
    individual_id: str = Schema(..., min_length=1, identity=True)
    taxonomy: Optional[str]
    gender: Optional[str]
    birth_date: Optional[date]
    death_date: Optional[date]
    ic_type: Optional[str]
    ic_version: Optional[float]
    ic_given_date: Optional[date]
    ic_withdrawn_date: Optional[date]
    ic_material: Optional[str]
    ic_data: Optional[str]
    ic_linking_ext: Optional[str]
    report_her_susc: Optional[str]
    report_inc_findings: Optional[str]
    diagnosis_count: Optional[int]
    age_first_diagnosis: Optional[int]


class Diagnosis(BaseModel):
    """
    Diagnosis entity
    """
    diagnosis_id: str = Schema(..., min_length=1, identity=True)
    individual_id: str = Schema(..., min_length=1, references='Individual')
    tumor_type: Optional[str]
    topography: Optional[str]
    treatment_protocol: Optional[str]
    tumor_stage: Optional[str]
    diagnosis_date: Optional[date]
    center_treatment: Optional[str]


class Biosource(BaseModel):
    """
    Biosource entity
    """
    biosource_id: str = Schema(..., min_length=1, identity=True)
    biosource_dedicated: Optional[str]
    individual_id: str = Schema(..., min_length=1, references='Individual')
    diagnosis_id: Optional[str] = Schema(None, min_length=1, references='Diagnosis')
    src_biosource_id: Optional[str] = Schema(None, min_length=1, references='Biosource')
    tissue: Optional[str]
    biosource_date: Optional[date]
    disease_status: Optional[str]
    tumor_percentage: Optional[int]


class Biomaterial(BaseModel):
    """
    Biomaterial entity
    """
    biomaterial_id: str = Schema(..., min_length=1, identity=True)
    src_biosource_id: str = Schema(..., min_length=1, references='Biosource')
    src_biomaterial_id: Optional[str] = Schema(None, min_length=1, references='Biomaterial')
    biomaterial_date: Optional[date]
    type: Optional[str]
    library_strategy: Optional[List[str]] = []
    analysis_type: Optional[List[str]] = []


class Study(BaseModel):
    """
    Study
    """
    study_id: str = Schema(..., min_length=1, identity=True)
    acronym: Optional[str]
    title: Optional[str]
    datadictionary: Optional[str]


class IndividualStudy(BaseModel):
    """
    Study to individual mapping
    """
    individual_study_id: int = Schema(..., identity=True)
    individual_id: str = Schema(..., min_length=1, references='Individual')
    study_id: str = Schema(..., min_length=1, references='Study')


SubjectEntity = Union[Individual, Diagnosis, Biosource, Biomaterial]


class CentralSubjectRegistry(BaseModel):
    """
    Central subject registry
    """
    individuals: Sequence[Individual]
    diagnoses: Optional[Sequence[Diagnosis]]
    biosources: Optional[Sequence[Biosource]]
    biomaterials: Optional[Sequence[Biomaterial]]

    @staticmethod
    def create(entity_data: Dict[str, Sequence[SubjectEntity]]):
        return CentralSubjectRegistry(
            individuals=entity_data['Individual'],
            diagnoses=entity_data['Diagnosis'],
            biosources=entity_data['Biosource'],
            biomaterials=entity_data['Biomaterial']
        )


StudyEntity = Union[Study, IndividualStudy]


class StudyRegistry(BaseModel):
    """
    Study registry
    """
    studies: Optional[Sequence[Study]]
    individual_studies: Optional[Sequence[IndividualStudy]]

    @staticmethod
    def create(entity_data: Dict[str, Sequence[StudyEntity]]):
        return StudyRegistry(
            studies=entity_data['Study'],
            individual_studies=entity_data['IndividualStudy']
        )
