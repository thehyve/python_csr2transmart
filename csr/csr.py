from datetime import datetime
from typing import Sequence, Optional

from pydantic import BaseModel


class Individual(BaseModel):
    """
    Individual entity
    """
    individual_id: str
    taxonomy: Optional[str]
    gender: Optional[str]
    birth_date: Optional[datetime]
    death_date: Optional[datetime]
    ic_type: Optional[bool]
    ic_version: Optional[float]
    ic_withdrawn_date: Optional[datetime]
    ic_material: Optional[bool]
    ic_data: Optional[bool]
    ic_linking_ext: Optional[bool]
    report_her_susc: Optional[bool]
    report_inc_findings: Optional[bool]


class Diagnosis(BaseModel):
    """
    Diagnosis entity
    """
    diagnosis_id: str
    individual_id: str
    tumor_type: Optional[str]
    topography: Optional[str]
    treatment_protocol: Optional[str]
    tumor_stage: Optional[str]
    diagnosis_date: Optional[datetime]
    center_treatment: Optional[str]


class Biosource(BaseModel):
    """
    Biosource entity
    """
    biosource_id: str
    biosource_dedicated: Optional[bool]
    individual_id: str
    diagnosis_id: str
    src_biosource_id: Optional[str]
    tissue: Optional[str]
    biosource_date: Optional[datetime]
    disease_status: Optional[str]
    tumor_percentage: Optional[int]


class Biomaterial(BaseModel):
    """
    Biomaterial entity
    """
    biomaterial_id: str
    src_biosource_id: str
    src_biomaterial_id: Optional[str]
    biomaterial_date: Optional[datetime]
    type: Optional[str]


class Study(BaseModel):
    """
    Study
    """
    study_id: str
    acronym: Optional[str]
    title: Optional[str]
    datadictionary: Optional[str]


class IndividualStudy(BaseModel):
    """
    Study to individual mapping
    """
    individual_study_id: int
    individual_id: str
    study_id: str


class CentralSubjectRegistry(BaseModel):
    """
    Central subject registry
    """
    individuals: Sequence[Individual]
    diagnoses: Optional[Sequence[Diagnosis]]
    biosources: Optional[Sequence[Biosource]]
    biomaterials: Optional[Sequence[Biomaterial]]


class StudyRegistry(BaseModel):
    """
    Study registry
    """
    studies: Optional[Sequence[Study]]
    individual_studies: Optional[Sequence[IndividualStudy]]
